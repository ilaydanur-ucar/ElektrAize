import os
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase config dosyasının yolu - proje kök dizininden
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRED_PATH = os.path.join(BASE_DIR, "firebase_config.json")

def initialize_firebase():
    if not firebase_admin._apps:
        # firebase_config.json dosyasını doğrudan kullan
        cred = credentials.Certificate(CRED_PATH)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Firestore client başlat
db = initialize_firebase()
