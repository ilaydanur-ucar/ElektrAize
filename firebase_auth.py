import os
from dotenv import load_dotenv
from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

# .env dosyasını yükle
load_dotenv()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    
    token = authorization.split(" ", 1)[1]
    
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except FirebaseError as e:
        raise HTTPException(status_code=401, detail=f"Firebase error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token verification failed")