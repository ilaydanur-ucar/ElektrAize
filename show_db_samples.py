import asyncio
import os
import json
import sys
from datetime import datetime

# ... imports

# Redirect stdout to a file
class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode, encoding='utf-8')
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()

# Start logging to file
sys.stdout = Tee('final_report.txt', 'w')

async def main():
    print("\n" + "="*60)
    print("VERITABANI BAGLANTI VE VERI DEMOSU")
    print("="*60)

    # ---------------------------------------------------------
    # 1. Supabase
    # ---------------------------------------------------------
    print("\n[1] SUPABASE ('model_results' tablosu)")
    print("-" * 40)
    try:
        from supabase_init import supabase
        response = supabase.table('model_results').select("*").limit(5).execute()
        
        if hasattr(response, 'data') and response.data:
            print(f"✅ Başarılı! {len(response.data)} kayıt çekildi:\n")
            print(json.dumps(response.data, indent=2, default=str))
        else:
            print("⚠️ Bağlantı başarılı ama veri yok veya boş döndü.")
    except Exception as e:
        print(f"❌ HATA: {e}")

    # ---------------------------------------------------------
    # 2. Firebase
    # ---------------------------------------------------------
    print("\n\n[2] FIREBASE (Firestore)")
    print("-" * 40)
    try:
        from firebase_init import db
        if db:
            # Koleksiyonları listele ve ilk bulduğundan örnek çek
            collections = db.collections()
            found_data = False
            
            # Generator olduğu için döngüyle bakmamız lazım
            for collection in collections:
                col_name = collection.id
                print(f"📂 Koleksiyon Bulundu: '{col_name}'")
                
                docs = collection.limit(5).stream()
                data_list = [doc.to_dict() for doc in docs]
                
                if data_list:
                    print(f"✅ '{col_name}' koleksiyonundan ilk {len(data_list)} veri:\n")
                    print(json.dumps(data_list, indent=2, default=str))
                    found_data = True
                    break # Sadece bir koleksiyon gösterip çıkalım
                else:
                    print(f"   (Bu koleksiyon boş)")
            
            if not found_data:
                print("⚠️ Hiçbir koleksiyonda veri bulunamadı veya koleksiyon yok.")
        else:
            print("❌ Firebase client başlatılamadı (firebase_init.py None döndü).")
            
    except Exception as e:
        error_str = str(e)
        if "datastore/setup" in error_str or "Cloud Firestore API" in error_str:
             print(f"❌ FIREBASE KURULUM GEREKİYOR: Firestore veritabanı oluşturulmamış.")
             print(f"   Lütfen Firebase/Google Cloud konsoluna gidip 'Create Database' diyerek Firestore'u 'Native Mode'da oluşturun.")
             print(f"   Hata detayı: {error_str[:100]}...")
        else:
            print(f"❌ HATA: {e}")
    print("-" * 40 + " [Firebase Bitti]")

    # ---------------------------------------------------------
    # 3. Redis
    # ---------------------------------------------------------
    print("\n\n[3] REDIS (Önbellek)")
    print("-" * 40)
    try:
        from redis_manager import redis_client
        pong = await redis_client.ping()
        if pong:
            keys = await redis_client.keys("*")
            print(f"✅ Bağlantı Başarılı! Toplam Anahtar Sayısı: {len(keys)}")
            
            if keys:
                print("\nÖrnek 5 Anahtar ve Değerleri:")
                for key in keys[:5]:
                    val_type = await redis_client.type(key)
                    val = await redis_client.get(key) if val_type == 'string' else f"[{val_type}]"
                    print(f" • {key}: {val[:50]}..." if len(str(val)) > 50 else f" • {key}: {val}")
        else:
            print("❌ Redis PING başarısız.")
    except Exception as e:
        print(f"❌ Redis henüz çalışmıyor (Hata: {e}).")
        print("   Not: Redis kritik değil, uygulama in-memory modda devam edebilir.")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
