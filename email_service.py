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