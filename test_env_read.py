"""
.env dosyasını okuma testi - detaylı
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# .env dosyasının yolunu belirle
env_path = Path(__file__).resolve().parent / ".env"

print("=" * 60)
print(".ENV DOSYASI OKUMA TESTİ")
print("=" * 60)

print(f"\n1. .env Dosyası Bilgileri:")
print(f"   Yol: {env_path}")
print(f"   Var mı: {'✅ EVET' if env_path.exists() else '❌ HAYIR'}")

if env_path.exists():
    print(f"   Boyut: {env_path.stat().st_size} byte")
    
    # Dosyayı ham olarak oku
    print(f"\n2. Dosya İçeriği (İlk 500 karakter):")
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("   " + "-" * 56)
            # İlk 500 karakteri göster, her satırı ayrı göster
            lines = content.split('\n')
            for i, line in enumerate(lines[:20], 1):  # İlk 20 satır
                # Hassas bilgileri gizle
                if '=' in line:
                    key, value = line.split('=', 1)
                    if value and len(value) > 10:
                        display_value = value[:10] + "..." + value[-5:] if len(value) > 15 else value[:10] + "..."
                    else:
                        display_value = value
                    print(f"   {i:2d}: {key}={display_value}")
                else:
                    print(f"   {i:2d}: {line}")
            if len(lines) > 20:
                print(f"   ... ({len(lines) - 20} satır daha)")
            print("   " + "-" * 56)
    except Exception as e:
        print(f"   ❌ Dosya okunamadı: {e}")

print(f"\n3. load_dotenv() Çağrısı:")
try:
    result = load_dotenv(dotenv_path=env_path, override=False)
    print(f"   Sonuç: {'✅ Başarılı' if result else '⚠️  Değişken bulunamadı'}")
except Exception as e:
    print(f"   ❌ Hata: {e}")

print(f"\n4. Ortam Değişkenleri (os.getenv ile):")
vars_to_check = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY", 
    "SUPABASE_KEY",
    "SUPABASE_DB_URL"
]

for var_name in vars_to_check:
    value = os.getenv(var_name)
    if value:
        # Değerin ilk ve son kısmını göster
        display_value = value[:20] + "..." + value[-10:] if len(value) > 30 else value[:30]
        print(f"   ✅ {var_name}: {display_value}")
    else:
        print(f"   ❌ {var_name}: NOT SET")

print(f"\n5. Tüm Ortam Değişkenleri (SUPABASE ile başlayanlar):")
supabase_vars = {k: v for k, v in os.environ.items() if 'SUPABASE' in k.upper()}
if supabase_vars:
    for key, value in supabase_vars.items():
        display_value = value[:20] + "..." + value[-10:] if len(value) > 30 else value[:30]
        print(f"   {key}: {display_value}")
else:
    print("   ⚠️  SUPABASE ile başlayan değişken bulunamadı")

print("\n" + "=" * 60)
print("TEST TAMAMLANDI")
print("=" * 60)

