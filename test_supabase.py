"""
Supabase bağlantı test scripti
Bu script Supabase URL ve KEY'in doğru olup olmadığını kontrol eder
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

# .env dosyasını yükle
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)

print("=" * 60)
print("SUPABASE BAĞLANTI TESTİ")
print("=" * 60)

# Değişkenleri al
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"\n1. .env Dosyası Konumu: {env_path}")
print(f"   Dosya var mı: {'✅ VAR' if env_path.exists() else '❌ YOK'}")

print(f"\n2. Ortam Değişkenleri:")
print(f"   SUPABASE_URL: {'✅ SET' if SUPABASE_URL else '❌ NOT SET'}")
if SUPABASE_URL:
    print(f"      Değer: {SUPABASE_URL[:30]}..." if len(SUPABASE_URL) > 30 else f"      Değer: {SUPABASE_URL}")

print(f"   SUPABASE_ANON_KEY: {'✅ SET' if SUPABASE_ANON_KEY else '❌ NOT SET'}")
if SUPABASE_ANON_KEY:
    print(f"      Değer: {SUPABASE_ANON_KEY[:30]}..." if len(SUPABASE_ANON_KEY) > 30 else f"      Değer: {SUPABASE_ANON_KEY}")

print(f"   SUPABASE_KEY: {'✅ SET' if SUPABASE_KEY else '❌ NOT SET'}")
if SUPABASE_KEY:
    print(f"      Değer: {SUPABASE_KEY[:30]}..." if len(SUPABASE_KEY) > 30 else f"      Değer: {SUPABASE_KEY}")

# Kullanılacak key'i belirle
key_to_use = SUPABASE_ANON_KEY or SUPABASE_KEY

print(f"\n3. Bağlantı Testi:")
if not SUPABASE_URL:
    print("   ❌ SUPABASE_URL bulunamadı!")
elif not key_to_use:
    print("   ❌ SUPABASE_ANON_KEY veya SUPABASE_KEY bulunamadı!")
else:
    try:
        print("   🔄 Supabase client oluşturuluyor...")
        supabase = create_client(SUPABASE_URL, key_to_use)
        print("   ✅ Client oluşturuldu!")
        
        print("   🔄 Basit bir test sorgusu yapılıyor...")
        # Basit bir test - herhangi bir tabloya SELECT yapmaya çalış
        # Eğer tablo yoksa, en azından bağlantının çalıştığını göreceğiz
        try:
            # Test için boş bir sorgu yapabiliriz veya bilinen bir tablo varsa onu kullanabiliriz
            result = supabase.table("_test_connection").select("*").limit(0).execute()
            print("   ✅ Bağlantı başarılı! (Test tablosu sorgulandı)")
        except Exception as table_error:
            # Tablo yoksa bu normal, önemli olan bağlantının çalışması
            error_msg = str(table_error)
            if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
                print("   ✅ Bağlantı başarılı! (Tablo bulunamadı ama bu normal)")
            elif "JWT" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                print(f"   ❌ KEY HATALI veya GEÇERSİZ!")
                print(f"      Hata: {error_msg}")
                print(f"\n   💡 ÇÖZÜM:")
                print(f"      1. Supabase Dashboard'a gidin: https://app.supabase.com")
                print(f"      2. Project Settings > API'ye gidin")
                print(f"      3. 'anon' veya 'public' key'i kopyalayın")
                print(f"      4. .env dosyasındaki SUPABASE_ANON_KEY'i güncelleyin")
            else:
                print(f"   ⚠️  Beklenmeyen hata: {error_msg}")
        
    except Exception as e:
        print(f"   ❌ BAĞLANTI HATASI!")
        print(f"      Hata Tipi: {type(e).__name__}")
        print(f"      Hata Mesajı: {str(e)}")
        
        error_msg = str(e).lower()
        if "url" in error_msg or "invalid" in error_msg:
            print(f"\n   💡 ÇÖZÜM:")
            print(f"      - SUPABASE_URL formatını kontrol edin")
            print(f"      - URL şu formatta olmalı: https://xxxxx.supabase.co")
        elif "key" in error_msg or "jwt" in error_msg or "unauthorized" in error_msg:
            print(f"\n   💡 ÇÖZÜM:")
            print(f"      1. Supabase Dashboard'a gidin: https://app.supabase.com")
            print(f"      2. Project Settings > API'ye gidin")
            print(f"      3. 'anon' veya 'public' key'i kopyalayın")
            print(f"      4. .env dosyasındaki SUPABASE_ANON_KEY'i güncelleyin")

print("\n" + "=" * 60)
print("TEST TAMAMLANDI")
print("=" * 60)

