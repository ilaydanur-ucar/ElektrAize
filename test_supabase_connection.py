"""
Supabase bağlantısını test et
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

# .env dosyasını yükle
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Ortam değişkenlerini al
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

print("=" * 60)
print("SUPABASE BAĞLANTI TESTİ")
print("=" * 60)
print(f"URL: {SUPABASE_URL}")
print(f"KEY: {SUPABASE_KEY[:30]}..." if SUPABASE_KEY else "KEY: BULUNAMADI")
print()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL veya SUPABASE_ANON_KEY bulunamadı!")
    exit(1)

try:
    print("🔄 Supabase client oluşturuluyor...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Client oluşturuldu!")
    print()
    
    print("🔄 Tabloları test ediyoruz...")
    
    # Test: genel_elektrik tablosundan 1 satır çek
    print("  - genel_elektrik tablosu test ediliyor...")
    result = supabase.table("genel_elektrik").select("*").limit(1).execute()
    print(f"    ✅ {len(result.data)} satır çekildi")
    
    # Test: weather tablosu
    print("  - weather tablosu test ediliyor...")
    result = supabase.table("weather").select("*").limit(1).execute()
    print(f"    ✅ {len(result.data)} satır çekildi")
    
    # Test: nufus tablosu
    print("  - nufus tablosu test ediliyor...")
    result = supabase.table("nufus").select("*").limit(1).execute()
    print(f"    ✅ {len(result.data)} satır çekildi")
    
    print()
    print("=" * 60)
    print("✅ TÜM TESTLER BAŞARILI!")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ HATA: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
