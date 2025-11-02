from supabase import create_client
import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# Ortam değişkenlerini al
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase istemcisini oluştur
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
