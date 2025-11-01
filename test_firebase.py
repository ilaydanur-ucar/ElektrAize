from firebase_init import db, auth

# Firestore'a test verisi yaz
db.collection("test").document("deneme1").set({"mesaj": "Merhaba Firebase!"})
print("✅ Firestore'a veri yazıldı")

# Authentication test (örnek bir kullanıcı mailiyle)
try:
    user = auth.get_user_by_email("test@ornek.com")
    print("Kullanıcı bulundu:", user.email)
except Exception as e:
    print("Kullanıcı bulunamadı:", e)
