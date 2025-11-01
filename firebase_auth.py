import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException, Header
from firebase_admin import auth as fb_auth

# .env dosyasını yükle
load_dotenv("bubir.env")  # Eğer adını .env yaptıysan sadece load_dotenv() yaz

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        decoded = fb_auth.verify_id_token(token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email"),
            "email_verified": decoded.get("email_verified", False),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


#  Yeni eklenen fonksiyon — doğrulama maili gönderme
def send_verification_email(id_token: str):
    if not FIREBASE_API_KEY:
        raise HTTPException(status_code=500, detail="Firebase API key bulunamadı")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    payload = {
        "requestType": "VERIFY_EMAIL",
        "idToken": id_token
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return {"message": "Doğrulama maili gönderildi"}
    else:
        print("Firebase error:", response.text)
        raise HTTPException(status_code=400, detail="Firebase doğrulama maili gönderilemedi.")