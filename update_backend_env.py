"""
Backend .env dosyasını frontend ile senkronize et
"""
from pathlib import Path

# Frontend .env'den bilgileri al
frontend_env = Path("frontend/.env")
backend_env = Path(".env")

# Frontend'den Supabase bilgilerini oku
supabase_url = None
supabase_anon_key = None

if frontend_env.exists():
    with open(frontend_env, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('VITE_SUPABASE_URL=') or line.startswith('SUPABASE_URL='):
                supabase_url = line.split('=', 1)[1].strip()
            elif line.startswith('VITE_SUPABASE_ANON_KEY=') or line.startswith('SUPABASE_ANON_KEY='):
                supabase_anon_key = line.split('=', 1)[1].strip()

print("Frontend'den okunan bilgiler:")
print(f"  URL: {supabase_url[:50] if supabase_url else 'BULUNAMADI'}...")
print(f"  KEY: {supabase_anon_key[:30] if supabase_anon_key else 'BULUNAMADI'}...")
print()

if not supabase_url or not supabase_anon_key:
    print("❌ Frontend'de gerekli bilgiler bulunamadı!")
    exit(1)

# Backend .env'i oku
backend_lines = []
if backend_env.exists():
    with open(backend_env, 'r', encoding='utf-8') as f:
        backend_lines = f.readlines()

# Supabase satırlarını güncelle
updated_lines = []
supabase_section_found = False
url_updated = False
key_updated = False

for line in backend_lines:
    stripped = line.strip()
    
    # SUPABASE_URL satırını güncelle
    if stripped.startswith('SUPABASE_URL='):
        updated_lines.append(f'SUPABASE_URL={supabase_url}\n')
        url_updated = True
    # SUPABASE_KEY veya SUPABASE_ANON_KEY satırını güncelle
    elif stripped.startswith('SUPABASE_KEY=') or stripped.startswith('SUPABASE_ANON_KEY='):
        if not key_updated:  # Sadece bir kez ekle
            updated_lines.append(f'SUPABASE_ANON_KEY={supabase_anon_key}\n')
            key_updated = True
    else:
        updated_lines.append(line)
    
    # SUPABASE bölümünü tespit et
    if '# --- SUPABASE ---' in line or '# SUPABASE' in line:
        supabase_section_found = True

# Eğer hiç eklenmemişse, SUPABASE bölümünü oluştur
if not url_updated or not key_updated:
    # SUPABASE bölümünü bul veya oluştur
    if not supabase_section_found:
        updated_lines.append('\n# --- SUPABASE ---\n')
    if not url_updated:
        updated_lines.append(f'SUPABASE_URL={supabase_url}\n')
    if not key_updated:
        updated_lines.append(f'SUPABASE_ANON_KEY={supabase_anon_key}\n')

# Backend .env'i yaz
with open(backend_env, 'w', encoding='utf-8') as f:
    f.writelines(updated_lines)

print("✅ Backend .env güncellendi!")
print(f"   SUPABASE_URL: {supabase_url[:50]}...")
print(f"   SUPABASE_ANON_KEY: {supabase_anon_key[:30]}...")
