# firebase_init.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Proje kökünden firebase_config.json dosyasının yolunu al
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CRED_PATH = os.path.join(BASE_DIR, "firebase_config.json")

# Uygulama zaten başlatılmadıysa başlat
if not firebase_admin._apps:
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred)

# Firestore (veritabanı) bağlantısı
db = firestore.client()
