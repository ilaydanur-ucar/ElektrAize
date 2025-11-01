import os
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase config dosyasının yolu
CRED_PATH = r"C:\Users\Sena Ceylan\OneDrive\Desktop\ElektrAize\firebase_config.json"

def initialize_firebase():
    if not firebase_admin._apps:
        # firebase_config.json dosyasını doğrudan kullan
        cred = credentials.Certificate(CRED_PATH)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Firestore client başlat
db = initialize_firebase()
