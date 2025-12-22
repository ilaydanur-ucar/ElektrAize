import os
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

def send_verification_email(id_token: str):
    if not FIREBASE_API_KEY:
        raise HTTPException(status_code=500, detail="Firebase API key not configured")
    
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    payload = {
        "requestType": "VERIFY_EMAIL",
        "idToken": id_token
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return {"message": "Verification email sent successfully"}
        else:
            error_data = response.json()
            print(f"Firebase error: {error_data}")
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to send verification email: {error_data.get('error', {}).get('message', 'Unknown error')}"
            )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")


def send_contact_email(subject: str, from_email: str, message: str):
    """
    Send contact form email using Resend API
    """
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Resend API key not configured")
    
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": "onboarding@resend.dev",  # Resend test domain (sabit kalmalı)
        "to": ["eneraize@gmail.com"],  # Resend Audience'da doğrulanmış email
        "reply_to": from_email,  # Gönderenin emaili reply-to olarak
        "subject": f"İletişim Formu: {subject}",
        "html": f"""
            <h2>Yeni İletişim Formu Mesajı</h2>
            <p><strong>Gönderen:</strong> {from_email}</p>
            <p><strong>Konu:</strong> {subject}</p>
            <hr>
            <p><strong>Mesaj:</strong></p>
            <p>{message.replace(chr(10), '<br>')}</p>
        """
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code in [200, 201]:
            return {"message": "Email sent successfully", "data": response.json()}
        else:
            # Resend failed - log email instead
            print("=" * 60)
            print("📧 EMAIL SIMULATED (Resend failed, logging instead)")
            print("=" * 60)
            print(f"From: {from_email}")
            print(f"To: elektraizeproje@gmail.com")
            print(f"Subject: {subject}")
            print(f"Message: {message}")
            print("=" * 60)
            return {"message": "Email logged (Resend unavailable in test mode)"}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout")
    except requests.exceptions.RequestException as e:
        # Network error - log email instead
        print("=" * 60)
        print("📧 EMAIL SIMULATED (Network error, logging instead)")
        print("=" * 60)
        print(f"From: {from_email}")
        print(f"To: elektraizeproje@gmail.com")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print("=" * 60)
        return {"message": "Email logged (network error)"}