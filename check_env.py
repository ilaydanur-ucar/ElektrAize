import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("=" * 50)
print("ENV DOSYASI KONTROLÜ")
print("=" * 50)
print(f"Env dosyası yolu: {env_path}")
print(f"Env dosyası var mı: {env_path.exists()}")
print()

keys_to_check = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_KEY']
for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # İlk 30 karakteri göster
        display = value[:30] + "..." if len(value) > 30 else value
        print(f"✅ {key}: {display}")
    else:
        print(f"❌ {key}: NOT SET")

print()
print("=" * 50)

# .env dosyasının içeriğini de göster (hassas bilgiler gizli)
if env_path.exists():
    print("ENV DOSYASI İÇERİĞİ:")
    print("=" * 50)
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Değeri gizle
                    display_value = value[:20] + "..." if len(value) > 20 else value
                    print(f"{key}={display_value}")
