# models.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# /me cevabı için basit şema
class MeResponse(BaseModel):
    uid: str
    email: Optional[EmailStr] = None
    email_verified: bool = False

# İstersen Firestore'da tutacağın kullanıcı profili
class UserProfile(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None
    # Pydantic v1/v2 fark etmez; ORM kullanmıyoruz

# Anomali satırı (eski projeyle uyumlu)
class AnomalyItem(BaseModel):
    sehir: str
    donem: str                # "YYYY-MM" veya tarih string
    gercek: float
    tahmin: float
    residual: float
    anomali: bool
    baseline: Optional[float] = None
    dev_pct: Optional[float] = None
    alt_limit: Optional[float] = None
    ust_limit: Optional[float] = None
    category: Optional[str] = None
