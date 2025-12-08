"""
Rate Limiting Test Script
Backend çalışırken bu script'i çalıştırın: python test_rate_limit.py
"""

import requests
import time
import concurrent.futures
from typing import List, Dict

BASE_URL = "http://127.0.0.1:8000"

def test_rate_limit_simple():
    """Basit rate limit testi - hızlı istekler"""
    print("\n" + "="*60)
    print("🚦 RATE LIMITING TESTİ")
    print("="*60)
    print(f"📍 Endpoint: {BASE_URL}/health")
    print(f"🎯 Hedef: 60 hızlı istek gönder (limit: 50/dakika)")
    print("="*60 + "\n")
    
    results = []
    rate_limit_hit = False
    
    # 60 hızlı istek gönder (her biri 0.1 saniye arayla)
    for i in range(1, 61):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            elapsed = time.time() - start
            
            status = response.status_code
            result = {
                'request': i,
                'status': status,
                'time': elapsed,
                'rate_limited': status == 429
            }
            
            if status == 429:
                rate_limit_hit = True
                result['message'] = response.json().get('error', {}).get('message', 'Rate Limited')
                print(f"⚠️  İstek #{i}: 429 RATE LIMITED - {result['message']}")
            elif status == 200:
                print(f"✅ İstek #{i}: 200 OK ({elapsed:.3f}s)", end="\r")
            else:
                print(f"❌ İstek #{i}: {status} ({elapsed:.3f}s)")
            
            results.append(result)
            time.sleep(0.1)  # 100ms bekleme
            
        except Exception as e:
            print(f"❌ İstek #{i} hatası: {e}")
            results.append({'request': i, 'status': 0, 'error': str(e)})
    
    # Sonuçları özetle
    print("\n" + "="*60)
    print("📊 SONUÇLAR")
    print("="*60)
    
    success_count = sum(1 for r in results if r.get('status') == 200)
    rate_limit_count = sum(1 for r in results if r.get('status') == 429)
    error_count = sum(1 for r in results if r.get('status') not in [200, 429] and r.get('status') != 0)
    
    print(f"✅ Başarılı (200): {success_count}/60")
    print(f"⚠️  Rate Limit (429): {rate_limit_count}/60")
    print(f"❌ Hata: {error_count}/60")
    
    if rate_limit_count > 0:
        print("\n🎉 RATE LIMITING ÇALIŞIYOR! ✅")
        print(f"   {rate_limit_count} istek başarıyla engellendi.")
    else:
        print("\n⚠️  Rate limit aşılmadı.")
        print("   Muhtemelen istekler çok yavaş gönderildi.")
        print("   Daha hızlı test için 'test_rate_limit_fast()' fonksiyonunu kullanın.")
    
    return results

def test_rate_limit_fast():
    """Hızlı rate limit testi - concurrent istekler"""
    print("\n" + "="*60)
    print("🚦 RATE LIMITING TESTİ (HIZLI)")
    print("="*60)
    print(f"📍 Endpoint: {BASE_URL}/health")
    print(f"🎯 Hedef: 60 eşzamanlı istek gönder")
    print("="*60 + "\n")
    
    results = []
    
    def make_request(index):
        try:
            start = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            elapsed = time.time() - start
            return {
                'request': index,
                'status': response.status_code,
                'time': elapsed,
                'rate_limited': response.status_code == 429,
                'data': response.json() if response.status_code != 429 else None
            }
        except Exception as e:
            return {'request': index, 'status': 0, 'error': str(e)}
    
    # 60 eşzamanlı istek gönder
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, 61)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            
            if result.get('status') == 429:
                print(f"⚠️  İstek #{result['request']}: 429 RATE LIMITED")
            elif result.get('status') == 200:
                print(f"✅ İstek #{result['request']}: 200 OK", end="\r")
            else:
                print(f"❌ İstek #{result['request']}: Status {result.get('status')}")
    
    # Sonuçları özetle
    print("\n" + "="*60)
    print("📊 SONUÇLAR")
    print("="*60)
    
    success_count = sum(1 for r in results if r.get('status') == 200)
    rate_limit_count = sum(1 for r in results if r.get('status') == 429)
    error_count = sum(1 for r in results if r.get('status') not in [200, 429] and r.get('status') != 0)
    
    print(f"✅ Başarılı (200): {success_count}/60")
    print(f"⚠️  Rate Limit (429): {rate_limit_count}/60")
    print(f"❌ Hata: {error_count}/60")
    
    if rate_limit_count > 0:
        print("\n🎉 RATE LIMITING ÇALIŞIYOR! ✅")
        print(f"   {rate_limit_count} istek başarıyla engellendi.")
        
        # İlk 429 hatasını detaylı göster
        first_429 = next((r for r in results if r.get('status') == 429), None)
        if first_429:
            print(f"\n📋 İlk engellenen istek detayları:")
            print(f"   İstek #: {first_429['request']}")
            print(f"   Status: 429 Too Many Requests")
            print(f"   Süre: {first_429.get('time', 0):.3f}s")
    else:
        print("\n⚠️  Rate limit aşılmadı.")
        print("   Backend'de rate limiting aktif olmayabilir.")
        print("   Kontrol: Backend loglarında 'Rate limiting middleware aktif' mesajını arayın.")
    
    return results

if __name__ == "__main__":
    print("\n🔍 Backend kontrolü yapılıyor...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend çalışıyor!\n")
        else:
            print(f"⚠️  Backend yanıt verdi ama status: {response.status_code}\n")
    except Exception as e:
        print(f"❌ Backend'e bağlanılamıyor: {e}")
        print("   Lütfen önce 'python main.py' ile backend'i başlatın.")
        exit(1)
    
    # Hızlı test öner
    print("İki test seçeneği var:")
    print("1. Hızlı test (eşzamanlı istekler) - Önerilen")
    print("2. Yavaş test (sıralı istekler)")
    
    choice = input("\nSeçiminiz (1/2, Enter=1): ").strip() or "1"
    
    if choice == "1":
        test_rate_limit_fast()
    else:
        test_rate_limit_simple()
    
    print("\n" + "="*60)
    print("✅ Test tamamlandı!")
    print("="*60)

