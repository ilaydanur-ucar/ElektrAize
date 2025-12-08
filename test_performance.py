"""
API Performans Testleri
Bu dosya mevcut sistemi değiştirmez, sadece performans ölçümü yapar.
Çalıştırmak için: python test_performance.py
"""

import time
import statistics
import requests
from typing import List, Dict
from datetime import datetime, timedelta

# Backend URL (backend çalışıyor olmalı)
BASE_URL = "http://127.0.0.1:8000"

class PerformanceTester:
    """API performans testleri için yardımcı sınıf"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: List[Dict] = []
    
    def test_endpoint(self, endpoint: str, method: str = "GET", 
                     params: dict = None, data: dict = None,
                     name: str = None, iterations: int = 10) -> Dict:
        """
        Bir endpoint'i birden fazla kez test eder ve istatistikleri döner
        
        Args:
            endpoint: Test edilecek endpoint (örn: "/health")
            method: HTTP method (GET, POST, vb.)
            params: Query parametreleri
            data: POST data
            name: Test adı (None ise endpoint kullanılır)
            iterations: Kaç kez test edilecek
        
        Returns:
            İstatistikler: min, max, avg, median, success_rate
        """
        if name is None:
            name = endpoint
        
        print(f"\n{'='*60}")
        print(f"🧪 Test: {name}")
        print(f"📍 Endpoint: {method} {endpoint}")
        print(f"🔄 İterasyon: {iterations} kez")
        print(f"{'='*60}")
        
        times = []
        errors = 0
        status_codes = []
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                if method.upper() == "GET":
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        params=params,
                        timeout=30
                    )
                elif method.upper() == "POST":
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        params=params,
                        json=data,
                        timeout=30
                    )
                else:
                    raise ValueError(f"Desteklenmeyen method: {method}")
                
                elapsed = time.time() - start_time
                times.append(elapsed)
                status_codes.append(response.status_code)
                
                if response.status_code >= 400:
                    errors += 1
                    print(f"  ⚠️  İterasyon {i+1}: {response.status_code} - {elapsed:.3f}s")
                else:
                    print(f"  ✅ İterasyon {i+1}: {response.status_code} - {elapsed:.3f}s")
                    
            except requests.exceptions.RequestException as e:
                errors += 1
                print(f"  ❌ İterasyon {i+1}: HATA - {str(e)}")
                times.append(None)
        
        # İstatistikleri hesapla
        valid_times = [t for t in times if t is not None]
        
        if not valid_times:
            print(f"  ❌ Tüm istekler başarısız!")
            return {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "error": "Tüm istekler başarısız"
            }
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "success_count": len(valid_times),
            "error_count": errors,
            "success_rate": (len(valid_times) / iterations) * 100,
            "min_time": min(valid_times),
            "max_time": max(valid_times),
            "avg_time": statistics.mean(valid_times),
            "median_time": statistics.median(valid_times),
            "status_codes": status_codes
        }
        
        # Sonuçları yazdır
        print(f"\n📊 Sonuçlar:")
        print(f"  ✅ Başarılı: {result['success_count']}/{iterations} ({result['success_rate']:.1f}%)")
        print(f"  ⏱️  Min: {result['min_time']:.3f}s")
        print(f"  ⏱️  Max: {result['max_time']:.3f}s")
        print(f"  ⏱️  Ortalama: {result['avg_time']:.3f}s")
        print(f"  ⏱️  Medyan: {result['median_time']:.3f}s")
        
        self.results.append(result)
        return result
    
    def test_concurrent_requests(self, endpoint: str, num_workers: int = 10,
                                 name: str = None) -> Dict:
        """
        Eşzamanlı (concurrent) istekler gönderir
        
        Args:
            endpoint: Test edilecek endpoint
            num_workers: Kaç eşzamanlı istek gönderilecek
            name: Test adı
        """
        import concurrent.futures
        
        if name is None:
            name = f"Concurrent ({num_workers}) - {endpoint}"
        
        print(f"\n{'='*60}")
        print(f"🧪 Test: {name}")
        print(f"📍 Endpoint: GET {endpoint}")
        print(f"👥 Eşzamanlı İstek: {num_workers}")
        print(f"{'='*60}")
        
        times = []
        errors = 0
        
        def make_request():
            try:
                start = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                elapsed = time.time() - start
                return {"time": elapsed, "status": response.status_code, "success": True}
            except Exception as e:
                return {"time": None, "status": None, "success": False, "error": str(e)}
        
        start_total = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(num_workers)]
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
                if result["success"]:
                    times.append(result["time"])
                    print(f"  ✅ İstek {i+1}: {result['status']} - {result['time']:.3f}s")
                else:
                    errors += 1
                    print(f"  ❌ İstek {i+1}: HATA - {result.get('error', 'Unknown')}")
        
        total_time = time.time() - start_total
        
        valid_times = [t for t in times if t is not None]
        
        if not valid_times:
            return {
                "name": name,
                "success": False,
                "error": "Tüm istekler başarısız"
            }
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "concurrent": num_workers,
            "total_time": total_time,
            "success_count": len(valid_times),
            "error_count": errors,
            "success_rate": (len(valid_times) / num_workers) * 100,
            "requests_per_second": num_workers / total_time,
            "min_time": min(valid_times),
            "max_time": max(valid_times),
            "avg_time": statistics.mean(valid_times),
            "median_time": statistics.median(valid_times)
        }
        
        print(f"\n📊 Sonuçlar:")
        print(f"  ✅ Başarılı: {result['success_count']}/{num_workers} ({result['success_rate']:.1f}%)")
        print(f"  ⏱️  Toplam Süre: {result['total_time']:.3f}s")
        print(f"  🚀 İstek/Saniye: {result['requests_per_second']:.2f}")
        print(f"  ⏱️  Ortalama: {result['avg_time']:.3f}s")
        print(f"  ⏱️  Medyan: {result['median_time']:.3f}s")
        
        self.results.append(result)
        return result
    
    def print_summary(self):
        """Tüm test sonuçlarının özetini yazdırır"""
        print(f"\n{'='*60}")
        print("📋 PERFORMANS TEST ÖZETİ")
        print(f"{'='*60}")
        
        for result in self.results:
            if result.get("success", True):
                print(f"\n✅ {result['name']}")
                print(f"   Ortalama: {result.get('avg_time', 0):.3f}s")
                print(f"   Başarı Oranı: {result.get('success_rate', 0):.1f}%")
                if 'requests_per_second' in result:
                    print(f"   İstek/Saniye: {result['requests_per_second']:.2f}")
            else:
                print(f"\n❌ {result['name']}")
                print(f"   Hata: {result.get('error', 'Unknown')}")


def main():
    """Ana test fonksiyonu"""
    print("🚀 ElektrAize API Performans Testleri Başlatılıyor...")
    print("⚠️  NOT: Backend'in çalışıyor olduğundan emin olun!")
    print(f"📍 Backend URL: {BASE_URL}\n")
    
    # Backend'in çalışıp çalışmadığını kontrol et
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend çalışmıyor veya /health endpoint'i hata veriyor!")
            print("   Lütfen önce backend'i başlatın: python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ Backend'e bağlanılamıyor!")
        print("   Lütfen önce backend'i başlatın: python main.py")
        return
    
    print("✅ Backend çalışıyor, testlere başlanıyor...\n")
    
    tester = PerformanceTester()
    
    print("="*60)
    print("📋 TEMEL ENDPOINT TESTLERİ")
    print("="*60)
    
    # 1. Health Check Testi (Ana)
    tester.test_endpoint("/health", name="Health Check (Ana)", iterations=20)
    
    # 2. Health Check Testi (Anomaly Router)
    tester.test_endpoint("/api/anomalies/health", name="Health Check (Anomaly)", iterations=20)
    
    # 3. Ana Sayfa Testi
    tester.test_endpoint("/", name="Ana Sayfa", iterations=20)
    
    # 4. Categories Endpoint Testi
    tester.test_endpoint("/api/anomalies/categories", name="Kategoriler", iterations=10)
    
    # 5. Cache State Testi
    tester.test_endpoint("/api/anomalies/cache/state", name="Cache Durumu", iterations=10)
    
    print("\n" + "="*60)
    print("🔐 AUTH GEREKTİREN ENDPOINT TESTLERİ")
    print("="*60)
    print("⚠️  NOT: Bu endpoint'ler Firebase auth gerektirir, 401 hatası normal!")
    print()
    
    # 6. Me Endpoint Testi (Auth gerekli)
    tester.test_endpoint("/me", name="Kullanıcı Bilgileri (/me)", iterations=5)
    
    # 7. Protected Test Endpoint (Auth gerekli, deprecated)
    tester.test_endpoint("/protected-test", name="Protected Test (deprecated)", iterations=5)
    
    # 8. Anomaly Detection Testi (Auth gerekli)
    tester.test_endpoint(
        "/api/anomalies",
        params={"kategori": "genel", "sehir": "ISTANBUL", "baslangic": "2024-01-01", "bitis": "2024-01-31"},
        name="Anomali Tespiti (ISTANBUL, genel)",
        iterations=5
    )
    
    # 9. Anomaly Scenarios Testi (Auth gerekli, POST)
    tester.test_endpoint(
        "/api/anomalies/scenarios",
        method="POST",
        data={
            "kategori": "genel",
            "sehir": "ISTANBUL",
            "baslangic": "2024-01-01",
            "bitis": "2024-01-31"
        },
        name="Anomali Senaryosu (POST)",
        iterations=3  # POST işlemi daha yavaş olabilir
    )
    
    # 10. Cache Invalidate Testi (POST)
    tester.test_endpoint(
        "/api/anomalies/cache/invalidate",
        method="POST",
        data={"sehir": "ISTANBUL", "kategori": "genel"},
        name="Cache Temizle (POST)",
        iterations=5
    )
    
    print("\n" + "="*60)
    print("🔥 EŞZAMANLI İSTEK TESTLERİ")
    print("="*60)
    
    # 11. Concurrent Requests - Health Check
    tester.test_concurrent_requests("/health", num_workers=10, name="Health Check (10 eşzamanlı)")
    tester.test_concurrent_requests("/health", num_workers=50, name="Health Check (50 eşzamanlı)")
    
    # 12. Concurrent Requests - Categories
    tester.test_concurrent_requests("/api/anomalies/categories", num_workers=10, name="Kategoriler (10 eşzamanlı)")
    
    # 13. Concurrent Requests - Cache State
    tester.test_concurrent_requests("/api/anomalies/cache/state", num_workers=10, name="Cache State (10 eşzamanlı)")
    
    # Özet
    tester.print_summary()
    
    print("\n✅ Performans testleri tamamlandı!")
    print("💡 İpucu: Ortalama süre < 1s ise iyi, < 0.5s ise çok iyi!")


if __name__ == "__main__":
    main()

