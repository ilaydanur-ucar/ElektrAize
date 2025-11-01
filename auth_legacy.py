# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Firebase'i bir kez initialize et
from firebase_init import db  # noqa: F401

# Firebase ID token doğrulama dependency
from firebase_auth import get_current_user

# ⛔️ Eski JWT router artık yok
# from auth import router as auth_router

# anomaly_api kendi içinde FastAPI(app) tanımlı; router değil.
# Bu yüzden alt uygulama (mount) ile ekleyeceğiz.
from anomaly_api import app as anomaly_subapp

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 ElektrAize API başlatılıyor...")
    yield
    print("🛑 ElektrAize API kapatılıyor...")

app = FastAPI(
    title="ElektrAize Energy Analytics (Gateway)",
    description="Ana API (Firebase Auth) + Anomali servisini mount eder",
    version="4.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # prod'da domainleri kısıtla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⛔️ Eski auth router'ı include etme
# app.include_router(auth_router)

# ✅ anomaly_api alt uygulama olarak köke mount.
# Böylece anomaly_api içindeki /health, /anomalies vb. path'ler aynen çalışır.
app.mount("/", anomaly_subapp)

# Gateway tarafı (çakışmasın diye /gw prefix'i)
@app.get("/gw/health")
def gw_health():
    return {"ok": True}

@app.get("/gw/me")
def gw_me(user = Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
    }

@app.get("/gw/protected-test")
def gw_protected(user = Depends(get_current_user)):
    return {"message": "Bu endpoint KORUMALI", "uid": user["uid"]}

