import re

# mapdata.js dosyasını oku
with open(r'c:\Users\Göksu\OneDrive\Desktop\elektraize\ElektrAize\frontend\public\html5countrymapv4.5\mapdata.js', 'r', encoding='utf-8') as f:
    content = f.read()

# state_specific bölümünü bul ve her şehir için url ekle
# Pattern: TR## şeklindeki şehir kodlarını bul
pattern = r'(TR\d+):\s*{\s*name:\s*"([^"]+)"(\s*,\s*url:\s*"[^"]*")?\s*}'

def add_url(match):
    state_id = match.group(1)
    city_name = match.group(2)
    # Eğer zaten url varsa değiştirme
    if match.group(3):
        return match.group(0)
    # Yoksa ekle
    return f'{state_id}: {{\n      name: "{city_name}",\n      url: "javascript:handleCityClick(\'{state_id}\', \'{city_name}\')"\n    }}'

# Değiştir
new_content = re.sub(pattern, add_url, content)

# Dosyaya yaz
with open(r'c:\Users\Göksu\OneDrive\Desktop\elektraize\ElektrAize\frontend\public\html5countrymapv4.5\mapdata.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Tüm 81 il için click event eklendi!")
