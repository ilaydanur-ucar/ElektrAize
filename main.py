# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from email_service import send_verification_email
from email_routes import router as firebase_router

# Firebase Admin SDK bir kez initialize (firebase_init.py içinde)
from firebase_init import db  # noqa: F401

# Firebase ID token doğrulama dependency
from firebase_auth import get_current_user

# Anomali servisi (kendi FastAPI(app) nesnesi)
from anomaly_api import app as anomaly_subapp



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 ElektrAize API başlatılıyor...")
    yield
    print("🛑 ElektrAize API kapatılıyor...")


app = FastAPI(
    title="ElektrAize Energy Analytics",
    description="Firebase Auth + Anomali Servisi",
    version="4.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # prod'da domain ile sınırla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(firebase_router)
# ⬇️ Anomali servisini alt path'e taşı (kökü kaplamasın)
app.mount("/anomaly", anomaly_subapp)

# --- Bearer Auth tanımı (sağlam sürüm) ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="ElektrAize Energy Analytics",
        version="4.0",
        description="Firebase Auth + Anomali Servisi",
        routes=app.routes,
    )

    # components/securitySchemes güvenli ekleme
    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    components["securitySchemes"] = security_schemes
    openapi_schema["components"] = components

    # Tüm API için default security tanımı (path'leri tek tek gezmeye gerek yok)
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
# ---------------- Gateway (kök) endpoint'leri ---------------- #

@app.get("/")
def root():
    return {
        "service": "ElektrAize Gateway",
        "docs": "/docs",
        "anomaly_docs": "/anomaly/docs",
        "health": "/health",
        "me": "/me",
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ElektrAize Gateway"}

@app.get("/me")
def get_me(user=Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
    }

@app.get("/protected-test")
def protected_test(user=Depends(get_current_user)):
    return {"message": "Bu endpoint korumalı", "uid": user["uid"]}

@app.post("/send-verification")
def send_verification(id_token: str):
    """
    Kullanıcıya Firebase üzerinden doğrulama maili gönderir.
    id_token frontend'den alınmalıdır.
    """
    return send_verification_email(id_token)

