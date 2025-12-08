from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasının yolunu açıkça belirt (proje root dizini)
env_path = Path(__file__).resolve().parent / ".env"

# .env dosyasını yükle
load_dotenv(dotenv_path=env_path, override=False)

# Ortam değişkenlerini al
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")  # SUPABASE_ANON_KEY veya SUPABASE_KEY kullan

# Supabase istemcisini oluştur
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL ve SUPABASE_ANON_KEY (veya SUPABASE_KEY) .env dosyasında tanımlanmalıdır!"
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
