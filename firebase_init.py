import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore, auth
from logging_config import get_logger

# Logger oluştur
logger = get_logger(__name__)

# Firebase config - use environment variable or relative path
def get_firebase_config_path():
    # Option 1: From environment variable
    env_path = os.getenv("FIREBASE_CONFIG_PATH")
    if env_path:
        return env_path
    
    # Option 2: Relative to this file
    return Path(__file__).parent / "firebase_config.json"

def initialize_firebase():
    if not firebase_admin._apps:
        config_path = get_firebase_config_path()
        try:
            if not Path(config_path).exists():
                logger.warning(f"Firebase config dosyası bulunamadı ({config_path})")
                logger.warning("Firebase özellikleri çalışmayabilir ama backend devam ediyor.")
                return None
            
            cred = credentials.Certificate(str(config_path))
            firebase_admin.initialize_app(cred)
        except Exception as e:
            logger.error(f"Firebase başlatma hatası: {e}", exc_info=True)
            return None
            
    try:
        return firestore.client()
    except:
        return None

# Firestore client başlat (Hata olsa da devam et)
db = initialize_firebase()

