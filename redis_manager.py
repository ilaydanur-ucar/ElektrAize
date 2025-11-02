import redis.asyncio as redis

# Redis istemcisi oluşturuluyor
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

async def test_connection():
    try:
        pong = await redis_client.ping()
        if pong:
            print("[REDIS] Bağlantı başarılı ✅")
        else:
            print("[REDIS] Bağlantı başarısız ❌")
    except Exception as e:
        print(f"[REDIS] Hata: {e}")
# --------------------------------------------------
# Önbellekleme (cache) işlemleri
# --------------------------------------------------

async def set_cache(key: str, value: str, expire_seconds: int = 60):
    """
    Belirtilen anahtar (key) için Redis'e veri kaydeder.
    expire_seconds: verinin ne kadar süre saklanacağını belirtir (varsayılan 60 saniye)
    """
    try:
        await redis_client.set(key, value, ex=expire_seconds)
        print(f"[CACHE] '{key}' anahtarı Redis'e kaydedildi ✅")
    except Exception as e:
        print(f"[CACHE-ERROR] Veri kaydedilemedi: {e}")

async def get_cache(key: str):
    """
    Redis'ten anahtara göre veri okur.
    """
    try:
        value = await redis_client.get(key)
        if value:
            print(f"[CACHE] '{key}' için veri bulundu: {value}")
        else:
            print(f"[CACHE] '{key}' anahtarı bulunamadı 🚫")
        return value
    except Exception as e:
        print(f"[CACHE-ERROR] Veri okunamadı: {e}")
        return None