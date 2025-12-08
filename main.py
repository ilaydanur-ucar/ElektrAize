# Logging setup - EN ÖNCE import et ve başlat
from logging_config import setup_logging, get_logger
setup_logging(level="INFO", log_to_file=True)
logger = get_logger(__name__)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from firebase_auth import get_current_user
from email_service import send_verification_email

# Error handling - logging'den sonra
from error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

# Firebase initialization
from firebase_init import db

# Anomaly router - en son (çünkü diğer modüllere bağımlı)
from anomaly_router import router as anomalies_router, load_all_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ElektrAize API baslatiliyor...")
    logger.info("="*60)
    logger.info("Tum modeller yukleniyor...")
    logger.info("="*60)
    load_all_models()
    logger.info("ElektrAize API hazir!")
    yield
    logger.info("ElektrAize API kapatiliyor...")

app = FastAPI(
    title="ElektrAize Energy Analytics API",
    description="""
    ElektrAize - Enerji Tüketimi Anomali Tespit Sistemi
    
    ## Özellikler
    
    * 🔍 **Anomali Tespiti**: Enerji tüketiminde anomali tespiti
    * 📊 **Senaryo Analizi**: Tarih aralığı bazlı detaylı analiz
    * 🏙️ **Şehir Bazlı Filtreleme**: İstanbul, Ankara, Kocaeli ve diğer şehirler
    * 📈 **Kategori Bazlı Analiz**: Mesken, aydınlanma, sanayi, tarımsal, vb.
    * 🔐 **Firebase Authentication**: Güvenli kullanıcı doğrulama
    * ⚡ **Redis Cache**: Popüler şehirler için optimize edilmiş cache
    
    ## Kategoriler
    
    * `genel` - Genel toplam tüketim
    * `mesken` - Mesken tüketimi
    * `aydinlatma` - Aydınlatma tüketimi
    * `sanayi` - Sanayi tüketimi
    * `tarimsal` - Tarımsal sulama tüketimi
    * `ticarethane` - Ticarethane tüketimi
    * `diger` - Diğer tüketimler
    
    ## Authentication
    
    Tüm endpoint'ler Firebase Authentication gerektirir.
    Authorization header'ında Bearer token gönderilmelidir.
    """,
    version="4.0",
    lifespan=lifespan,
    contact={
        "name": "ElektrAize Team",
    },
    license_info={
        "name": "MIT",
    },
)

# ===================== ERROR HANDLERS =====================
# Merkezi error handling - tüm exception'lar burada yakalanır
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ===================== RATE LIMITING =====================
# API koruma - kötü niyetli kullanıcılara ve DDoS saldırılarına karşı
# NOT: Rate limiting middleware'i CORS'dan ÖNCE eklenmelidir
try:
    from rate_limiter import setup_rate_limiter, limiter
    setup_rate_limiter(app)
except ImportError:
    logger.warning("slowapi paketi yüklü değil. Rate limiting devre dışı. Yüklemek için: pip install slowapi")
    limiter = None
except Exception as e:
    logger.warning(f"Rate limiting başlatılamadı: {e}")
    limiter = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domain'lerle değiştirin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    components["securitySchemes"] = security_schemes
    openapi_schema["components"] = components
    
    # Global security - tüm endpoint'ler için
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Anomali router'ını ekle
app.include_router(anomalies_router)

# ===================== ROUTES =====================

@app.get(
    "/",
    summary="API Ana Sayfa",
    description="ElektrAize Energy Analytics API'nin ana endpoint'i. Mevcut endpoint'leri ve versiyon bilgisini döndürür.",
    tags=["System"]
)
def root():
    """
    API ana sayfa - servis bilgileri ve endpoint listesi.
    """
    return {
        "service": "ElektrAize Energy Analytics API",
        "version": "4.0",
        "docs": "/docs",
        "health": "/health",
        "me": "/me",
        "anomalies": "/api/anomalies",
    }

@app.get(
    "/health",
    summary="Sağlık Kontrolü",
    description="API servisinin genel sağlık durumunu kontrol eder",
    tags=["System"]
)
def health():
    """
    Ana servis sağlık kontrolü.
    
    API'nin çalışıp çalışmadığını kontrol eder.
    """
    return {
        "status": "healthy", 
        "service": "ElektrAize Energy Analytics API",
        "version": "4.0"
    }

@app.get(
    "/me",
    summary="Kullanıcı Bilgileri",
    description="Mevcut kullanıcının Firebase Authentication bilgilerini döndürür",
    tags=["Authentication"]
)
def get_me(user=Depends(get_current_user)):
    """
    Kullanıcı bilgileri endpoint'i.
    
    Firebase Authentication token'ından kullanıcı bilgilerini çıkarır.
    """
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
    }

@app.get(
    "/protected-test",
    summary="Korumalı Endpoint Testi",
    description="Authentication'ın çalışıp çalışmadığını test eder",
    tags=["Authentication", "Debug"],
    deprecated=True
)
def protected_test(user=Depends(get_current_user)):
    """
    Korumalı endpoint testi (debug amaçlı).
    """
    return {"message": "This is a protected endpoint", "uid": user["uid"]}

@app.post(
    "/send-verification",
    summary="E-posta Doğrulama Gönder",
    description="Kullanıcıya Firebase üzerinden e-posta doğrulama linki gönderir",
    tags=["Authentication"]
)
def send_verification(id_token: str):
    """
    E-posta doğrulama gönderme endpoint'i.
    
    Firebase Authentication kullanarak kullanıcıya doğrulama e-postası gönderir.
    id_token frontend'den alınmalıdır.
    """
    return send_verification_email(id_token)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)