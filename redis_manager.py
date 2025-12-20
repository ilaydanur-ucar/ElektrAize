import redis.asyncio as redis
import asyncio
import os
import json
from typing import Any, Optional, Dict
from datetime import datetime
from logging_config import get_logger

# Logger oluştur
logger = get_logger(__name__)

# Redis istemcisi oluşturuluyor - environment variables kullanarak
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
)

# Popüler şehirler - daha uzun cache süresi
POPULAR_CITIES = {"ANKARA", "ISTANBUL", "KOCAELI", "IZMIR", "BURSA", "ANTALYA", "ADANA"}
POPULAR_CITY_TTL = 3600  # 1 saat
NORMAL_CITY_TTL = 1800   # 30 dakika
DEFAULT_TTL = 600        # 10 dakika

# Cache metrikleri
cache_stats = {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "errors": 0
}

async def test_connection():
    try:
        pong = await redis_client.ping()
        if pong:
            logger.info("Redis bağlantısı başarılı ✅")
        else:
            logger.error("Redis bağlantısı başarısız ❌")
    except Exception as e:
        logger.error(f"Redis bağlantı hatası: {e}", exc_info=True)

# --------------------------------------------------
# Cache Key Generation
# --------------------------------------------------

def generate_cache_key(prefix: str, **kwargs) -> str:
    """Cache key oluştur - kategori+şehir+tarih bazında"""
    parts = [prefix]
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}:{str(value).lower().replace(' ', '_')}")
    return ":".join(parts)

def get_cache_ttl(city: Optional[str] = None) -> int:
    """Şehir bazında TTL belirle - popüler şehirler için daha uzun"""
    if city and city.upper() in POPULAR_CITIES:
        return POPULAR_CITY_TTL
    elif city:
        return NORMAL_CITY_TTL
    else:
        return DEFAULT_TTL

# --------------------------------------------------
# Önbellekleme (cache) işlemleri - Geliştirilmiş
# --------------------------------------------------

async def set_cache(key: str, value: Any, expire_seconds: Optional[int] = None, city: Optional[str] = None):
    """
    Redis'e veri kaydet - JSON serialization ile
    """
    try:
        # TTL belirle
        if expire_seconds is None:
            expire_seconds = get_cache_ttl(city)
        
        # JSON'a çevir
        if isinstance(value, (dict, list)):
            serialized_value = json.dumps(value, default=str, ensure_ascii=False)
        else:
            serialized_value = str(value)
        
        await redis_client.set(key, serialized_value, ex=expire_seconds)
        cache_stats["sets"] += 1
        logger.debug(f"Cache kaydedildi: {key} (TTL: {expire_seconds}s)")
        return True
    except Exception as e:
        cache_stats["errors"] += 1
        logger.error(f"Cache kayıt hatası: {key} - {e}", exc_info=True)
        return False

async def get_cache(key: str) -> Optional[Any]:
    """
    Redis'ten veri oku - JSON deserialization ile
    """
    try:
        value = await redis_client.get(key)
        if value:
            cache_stats["hits"] += 1
            logger.info(f"Cache hit: {key} ✅")
            # JSON parse dene
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            cache_stats["misses"] += 1
            logger.info(f"Cache miss: {key} 🚫")
        return None
    except Exception as e:
        cache_stats["errors"] += 1
        logger.error(f"Cache okuma hatası: {key} - {e}", exc_info=True)
        return None

async def delete_cache(key: str) -> bool:
    """Cache'den veri sil"""
    try:
        await redis_client.delete(key)
        logger.debug(f"Cache silindi: {key}")
        return True
    except Exception as e:
        logger.error(f"Cache silme hatası: {key} - {e}", exc_info=True)
        return False

async def delete_cache_pattern(pattern: str) -> int:
    """Pattern'e uyan tüm cache'leri sil"""
    try:
        keys = await redis_client.keys(pattern)
        if keys:
            deleted = await redis_client.delete(*keys)
            logger.debug(f"Cache pattern silindi: {pattern} - {deleted} key silindi")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Cache pattern silme hatası: {pattern} - {e}", exc_info=True)
        return 0

async def get_cache_stats() -> Dict[str, Any]:
    """Cache istatistiklerini döndür"""
    total = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = (cache_stats["hits"] / total * 100) if total > 0 else 0
    
    return {
        "hits": cache_stats["hits"],
        "misses": cache_stats["misses"],
        "sets": cache_stats["sets"],
        "errors": cache_stats["errors"],
        "hit_rate": round(hit_rate, 2),
        "total_requests": total,
        "popular_cities": list(POPULAR_CITIES)
    }

async def reset_cache_stats():
    """Cache istatistiklerini sıfırla"""
    global cache_stats
    cache_stats = {"hits": 0, "misses": 0, "sets": 0, "errors": 0}
    logger.debug("Cache istatistikleri sıfırlandı")

# Cache invalidation stratejileri
async def invalidate_anomaly_cache(category: Optional[str] = None, city: Optional[str] = None):
    """Anomali cache'lerini invalidate et"""
    try:
        if category and city:
            pattern = f"anomaly:{category}:city:{city.upper()}:*"
        elif category:
            pattern = f"anomaly:{category}:*"
        elif city:
            pattern = f"anomaly:*:city:{city.upper()}:*"
        else:
            pattern = "anomaly:*"
        
        deleted = await delete_cache_pattern(pattern)
        logger.info(f"Anomali cache temizlendi: {deleted} key (pattern: {pattern})")
        return deleted
    except Exception as e:
        logger.error(f"Anomali cache invalidation hatası: {e}", exc_info=True)
        return 0

async def invalidate_scenario_cache(category: Optional[str] = None, city: Optional[str] = None):
    """Senaryo cache'lerini invalidate et"""
    try:
        if category and city:
            pattern = f"scenario:{category}:city:{city.upper()}:*"
        elif category:
            pattern = f"scenario:{category}:*"
        elif city:
            pattern = f"scenario:*:city:{city.upper()}:*"
        else:
            pattern = "scenario:*"
        
        deleted = await delete_cache_pattern(pattern)
        logger.info(f"Senaryo cache temizlendi: {deleted} key (pattern: {pattern})")
        return deleted
    except Exception as e:
        logger.error(f"Senaryo cache invalidation hatası: {e}", exc_info=True)
        return 0

if __name__ == "__main__":
    asyncio.run(test_connection())
