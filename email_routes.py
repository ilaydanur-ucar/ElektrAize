# firebase_routes.py (veya mevcut routes dosyan)
import os, requests
from fastapi import APIRouter, HTTPException

router = APIRouter()
API_KEY = os.getenv("FIREBASE_WEB_API_KEY")  # .env'de bu isimle dursun

@router.post("/send-verification")
def send_verification(id_token: str):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"
    payload = {"requestType": "VERIFY_EMAIL", "idToken": id_token}
    r = requests.post(url, json=payload, timeout=10)

    # Hataları gizleme! Google’ın mesajını aynen döndürelim:
    if not r.ok:
        try:
            msg = r.json().get("error", {}).get("message", "UNKNOWN_ERROR")
        except Exception:
            msg = r.text
        raise HTTPException(status_code=400, detail=msg)

    # Başarı
    data = r.json()  # {"email": "..."} döner
    return {"status": "ok", "email": data.get("email")}


@router.post("/send-contact-email")
def send_contact(subject: str, from_email: str, message: str):
    """
    Contact form endpoint - sends email via Resend
    """
    from email_service import send_contact_email
    
    try:
        result = send_contact_email(subject, from_email, message)
        return {"status": "ok", "message": "Email sent successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
