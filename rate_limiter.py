"""
Rate Limiting Middleware
API'yi kötü niyetli kullanıcılara ve DDoS saldırılarına karşı korur.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse
import os
from logging_config import get_logger

logger = get_logger(__name__)

# Redis bağlantısı - mevcut Redis client'ı kullan
# Redis bağlantı bilgileri
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_url = os.getenv("REDIS_URL")

# Limiter oluştur - Redis varsa kullan, yoksa in-memory
# Önce in-memory ile başlat (Redis bağlantı hatalarını önlemek için)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/hour", "50/minute"],
    auto_check=True  # Tüm endpoint'lere otomatik uygula
)

# Redis varsa ve bağlanabiliyorsa kullan
try:
    if redis_url:
        storage_uri = redis_url
    else:
        storage_uri = f"redis://{redis_host}:{redis_port}"
    
    # Redis'i test et
    import redis
    test_client = redis.from_url(storage_uri, socket_connect_timeout=2)
    test_client.ping()
    test_client.close()
    
    # Redis çalışıyorsa, limiter'ı Redis ile yeniden oluştur
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["200/hour", "50/minute"],
        auto_check=True,
        in_memory_fallback_enabled=True  # Redis down olursa in-memory'e geç
    )
    logger.info(f"Rate limiter Redis ile başlatıldı: {storage_uri}")
    
except ImportError:
    logger.warning("redis paketi yüklü değil. In-memory rate limiting kullanılıyor.")
except Exception as e:
    logger.warning(f"Redis bağlantısı başarısız, in-memory kullanılacak: {e}")
    # Zaten in-memory limiter oluşturuldu, devam et


# Rate limit aşıldığında dönecek response
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Rate limit aşıldığında dönecek özel error response
    """
    # exc.detail güvenli şekilde al
    detail = getattr(exc, 'detail', str(exc)) if hasattr(exc, 'detail') else str(exc)
    
    logger.warning(
        f"Rate limit aşıldı: IP={get_remote_address(request)} | "
        f"Path={request.url.path} | Limit={detail}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "type": "RateLimitExceeded",
                "message": "Çok fazla istek gönderildi. Lütfen daha sonra tekrar deneyin.",
                "details": detail,
                "retry_after": getattr(exc, 'retry_after', 60) if hasattr(exc, 'retry_after') else 60
            }
        },
        headers={
            "Retry-After": str(getattr(exc, 'retry_after', 60) if hasattr(exc, 'retry_after') else 60),
            "X-RateLimit-Limit": detail.split("/")[0] if "/" in detail else "50",
            "X-RateLimit-Remaining": "0"
        }
    )


# Rate limit exception handler'ı kaydet
def setup_rate_limiter(app):
    """
    Rate limiter'ı FastAPI app'e entegre et
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    
    # ASGI Middleware ekle - default_limits'in çalışması için gerekli
    app.add_middleware(SlowAPIASGIMiddleware)
    
    logger.info("Rate limiting middleware aktif ✅")
# Farklı endpoint'ler için özel limitler
# Decorator olarak kullanılabilir: @rate_limit("10/minute")

def rate_limit(limit: str):
    """
    Endpoint için özel rate limit belirle
    
    Örnek kullanım:
    @app.get("/api/anomalies")
    @rate_limit("30/minute")
    def get_anomalies(...):
        ...
    """
    return limiter.limit(limit)

# Limiter'ı export et - endpoint'lerde kullanmak için
__all__ = ['limiter', 'setup_rate_limiter', 'rate_limit']

