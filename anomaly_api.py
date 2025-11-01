# anomaly_api.py
# -*- coding: utf-8 -*-
"""
ElektrAize Anomaly API - Tam Çalışan Versiyon
"""
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

from firebase_auth import get_current_user
from typing import Dict

from veri_cek import (
    get_train_test,         
    get_processed_frames,   
    DATE_COL, CITY_COL
)


# -----------------------------------------------------------------------------
# FastAPI kurulum
# -----------------------------------------------------------------------------
app = FastAPI(title="ElektrAize Anomaly API", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# -----------------------------------------------------------------------------
# Data Modeller
# -----------------------------------------------------------------------------
class AnomalyItem(BaseModel):
    sehir: str
    donem: str
    gercek: float
    tahmin: float
    residual: float
    anomali: bool
    baseline: Optional[float] = None
    dev_pct: Optional[float] = None
    alt_limit: Optional[float] = None
    ust_limit: Optional[float] = None
    category: Optional[str] = None

# Tüm tüketim kategorileri - BOŞLUKSUZ ve DOĞRU
CONSUMPTION_CATEGORIES = {
    "genel": "Genel_Toplam_MWh",
    "aydinlatma": "Aydinlatma_MWh", 
    "mesken": "Mesken_MWh",
    "sanayi": "Sanayi_MWh",
    "tarimsal": "Tarımsal_Sulama_MWh",
    "ticarethane": "Ticarethane_MWh",
    "diger": "Diger_MWh"
}

# Global model dictionary
MODELS = {}

# -----------------------------------------------------------------------------
# MODEL YÜKLEME - GELİŞTİRİLMİŞ
# -----------------------------------------------------------------------------
def load_all_models():
    """Tüm kategoriler için model yükle - Geliştirilmiş versiyon"""
    global MODELS
    
    for category_name, target_col in CONSUMPTION_CATEGORIES.items():
        try:
            print(f"\n[MODEL] {category_name} için model yükleniyor...")
            print(f"[MODEL] Target column: {target_col}")
            
            # Veri kontrolü
            Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
            
            print(f"[MODEL] Veri boyutları - Xtr: {Xtr.shape}, Xte: {Xte.shape}")
            
            if len(Xtr) == 0 or len(Xte) == 0:
                print(f"[UYARI] {category_name} için yeterli veri yok, atlanıyor...")
                MODELS[category_name] = None
                continue
            
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(Xtr, ytr)
            
            # Model başarısını kontrol et
            train_score = model.score(Xtr, ytr)
            test_score = model.score(Xte, yte) if len(Xte) > 0 else 0
            
            MODELS[category_name] = {
                'model': model,
                'target_col': target_col,
                'train_score': train_score,
                'test_score': test_score
            }
            
            print(f"[OK] {category_name} modeli yüklendi - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
            
        except Exception as e:
            print(f"[ERROR] {category_name} modeli yüklenemedi: {str(e)}")
            MODELS[category_name] = None

# -----------------------------------------------------------------------------
# ANOMALİ TESPİTİ - GELİŞTİRİLMİŞ
# -----------------------------------------------------------------------------
def detect_anomalies(gercek: pd.Series, baseline: pd.Series, tolerance_pct: float = 0.10):
    """Geliştirilmiş anomali tespiti"""
    # Baseline sıfır değerlerini önle
    baseline_safe = baseline.replace(0, 1e-8)
    
    alt_limit = baseline_safe * (1 - tolerance_pct)
    ust_limit = baseline_safe * (1 + tolerance_pct)
    
    anomalies = ((gercek < alt_limit) | (gercek > ust_limit)) & baseline.notna()
    return anomalies, alt_limit, ust_limit

# -----------------------------------------------------------------------------
# ENDPOINT'LER - TAMAMEN YENİLENDİ
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında tüm modelleri yükle"""
    print("\n" + "="*60)
    print("[STARTUP] Tüm modeller yükleniyor...")
    print("="*60)
    
    load_all_models()
    
    loaded_count = sum(1 for m in MODELS.values() if m is not None)
    print(f"\n[STARTUP] {loaded_count}/{len(CONSUMPTION_CATEGORIES)} model yüklendi")
    
    # Yüklenen modelleri göster
    for category, model_info in MODELS.items():
        status = "YÜKLENDİ" if model_info is not None else "YÜKLENMEDİ"
        if model_info:
            print(f"  ✓ {category}: R²={model_info.get('train_score', 0):.3f}")
        else:
            print(f"  ✗ {category}: Model yüklenemedi")

@app.get("/")
def read_root():
    loaded_count = sum(1 for m in MODELS.values() if m is not None)
    return {
        "message": "ElektrAize Multi-Category Anomaly API",
        "version": "3.0",
        "available_categories": list(CONSUMPTION_CATEGORIES.keys()),
        "models_loaded": f"{loaded_count}/{len(CONSUMPTION_CATEGORIES)}",
        "status": "ready"
    }

@app.get("/health")
def health():
    loaded_count = sum(1 for m in MODELS.values() if m is not None)
    return {
        "status": "ok" if loaded_count > 0 else "error",
        "loaded_models": loaded_count,
        "total_categories": len(CONSUMPTION_CATEGORIES),
        "available_categories": [cat for cat, model in MODELS.items() if model is not None]
    }

@app.get("/categories")
def get_categories():
    """Tüm kategorileri listele"""
    loaded_models = {cat: (model is not None) for cat, model in MODELS.items()}
    loaded_details = {}
    
    for cat, model_info in MODELS.items():
        if model_info:
            loaded_details[cat] = {
                "loaded": True,
                "train_score": model_info.get('train_score', 0),
                "test_score": model_info.get('test_score', 0),
                "target_column": model_info.get('target_col', '')
            }
        else:
            loaded_details[cat] = {"loaded": False}
    
    return {
        "available_categories": list(CONSUMPTION_CATEGORIES.keys()),
        "models_loaded": loaded_models,
        "details": loaded_details
    }

@app.get("/anomalies", response_model=List[AnomalyItem])
def anomalies(
    category: str = Query("genel", description="Tüketim kategorisi"),
    city: Optional[str] = Query(None, description="Şehir adı (BÜYÜK HARF ve İngilizce karakterlerle)"),
    start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD"),
    tolerance_pct: float = Query(0.10, description="Tolerans yüzdesi"),
    debug: bool = Query(False, description="Debug bilgilerini göster"),
    current_user: Dict = Depends(get_current_user)  # Bu satırı ekliyoruz
):
    """
    GELİŞTİRİLMİŞ ANOMALİ TESPİTİ
    - Kategori adı boşluk kontrolü
    - Detaylı hata yönetimi  
    - Geliştirilmiş debug modu
    """
    try:
      
        # Kategori adını temizle (baştaki/sondaki boşlukları kaldır)
        category = category.strip().lower()
        
        print(f"\n[ANOMALI] Yeni istek - Kategori: '{category}', Şehir: {city}")
        
         # Model kontrolü - TEMİZLENMİŞ category İLE KONTROL ET
        if category not in MODELS or MODELS[category] is None:
            available_cats = [cat for cat, model in MODELS.items() if model is not None]
            raise HTTPException(
                status_code=400, 
                detail=f"'{category}' kategorisi için model yüklenmemiş. Mevcut kategoriler: {available_cats}"
            )
        
        # ... KODUN GERİ KALANI AYNEN KALACAK ...
        model_info = MODELS[category]
        target_col = model_info['target_col']
        model = model_info['model']
        
        print(f"[MODEL] {category} modeli kullanılıyor - Target: {target_col}")

        # Verileri yükle
        df_train, df_test = get_processed_frames(target_col=target_col)
        # ... mevcut kodun geri kalanı AYNEN kalacak ...

        # Model kontrolü - geliştirilmiş
        if category not in CONSUMPTION_CATEGORIES:
            available_cats = list(CONSUMPTION_CATEGORIES.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"'{category}' kategorisi bulunamadı. Mevcut kategoriler: {available_cats}"
            )
        
        if category not in MODELS or MODELS[category] is None:
            available_cats = [cat for cat, model in MODELS.items() if model is not None]
            raise HTTPException(
                status_code=400, 
                detail=f"'{category}' kategorisi için model yüklenmemiş. Mevcut kategoriler: {available_cats}"
            )
        
        model_info = MODELS[category]
        target_col = model_info['target_col']
        model = model_info['model']
        
        print(f"[MODEL] {category} modeli kullanılıyor - Target: {target_col}")

        # Verileri yükle
        df_train, df_test = get_processed_frames(target_col=target_col)
        Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
        
        if debug:
            print(f"[DEBUG] Veri boyutları - Train: {df_train.shape}, Test: {df_test.shape}")
            print(f"[DEBUG] X_train: {Xtr.shape}, X_test: {Xte.shape}, y_test: {yte.shape}")
            if CITY_COL in df_test.columns:
                cities_in_test = df_test[CITY_COL].unique()
                print(f"[DEBUG] Test verisindeki şehir sayısı: {len(cities_in_test)}")
                print(f"[DEBUG] İlk 10 şehir: {cities_in_test[:10]}")
                if city:
                    city_data = df_test[df_test[CITY_COL] == city]
                    print(f"[DEBUG] '{city}' şehri için kayıt sayısı: {len(city_data)}")

        # Baseline hesapla
        df_train = df_train.copy()
        df_train["ay"] = pd.to_datetime(df_train[DATE_COL]).dt.month
        seasonal_baseline = (
            df_train.groupby([CITY_COL, "ay"])[target_col]
            .mean()
            .rename("baseline")
            .reset_index()
        )

        # Test verisine baseline'ı ekle
        df_test = df_test.copy()
        df_test["ay"] = pd.to_datetime(df_test[DATE_COL]).dt.month
        df_test = df_test.merge(seasonal_baseline, on=[CITY_COL, "ay"], how="left")

        # Model tahminleri
        yhat = model.predict(Xte)
        
        # Verileri hazırla - index uyumluluğu için
        df_test_reset = df_test.reset_index(drop=True)
        min_len = min(len(df_test_reset), len(yte), len(yhat))
        
        df_test_ordered = df_test_reset.head(min_len).copy()
        yte_series = pd.Series(yte.values[:min_len])
        yhat_series = pd.Series(yhat[:min_len])
        baseline_series = df_test_ordered["baseline"].reset_index(drop=True)

        print(f"[ISLENEN] {category} - {min_len} kayıt işlendi")

        # Anomali tespiti
        flags_anomali, alt_limit, ust_limit = detect_anomalies(
            yte_series, baseline_series, tolerance_pct
        )

        # Sonuçları hazırla
        out = pd.DataFrame({
            "sehir": df_test_ordered[CITY_COL].astype(str),
            "donem": pd.to_datetime(df_test_ordered[DATE_COL]).dt.strftime("%Y-%m-%d"),
            "gercek": yte_series.astype(float),
            "tahmin": yhat_series.astype(float),
            "residual": (yte_series - yhat_series).astype(float),
            "anomali": flags_anomali.astype(bool),
            "baseline": baseline_series.astype(float),
            "dev_pct": ((yte_series - baseline_series) / baseline_series.replace(0, 1e-8)).astype(float),
            "alt_limit": alt_limit.astype(float),
            "ust_limit": ust_limit.astype(float),
            "category": category
        })

        # Filtreleme - GELİŞTİRİLMİŞ
        original_count = len(out)
        filtered_count = original_count
        
        if city:
            # Büyük harf tam eşleşme
            city_mask = out["sehir"] == city
            filtered_out = out[city_mask]
            filtered_count = len(filtered_out)
            
            print(f"[FILTRE] Şehir: '{city}' -> {filtered_count} kayıt (önce: {original_count})")
            
            # Eğer hiç kayıt yoksa, şehir ismini kontrol et
            if filtered_count == 0:
                available_cities = sorted(out["sehir"].unique()) if original_count > 0 else []
                similar_cities = [c for c in available_cities if city.upper() in c.upper()] if available_cities else []
                
                print(f"[UYARI] '{city}' şehri bulunamadı!")
                print(f"[UYARI] Mevcut şehirler ({len(available_cities)}): {available_cities[:10]}{'...' if len(available_cities) > 10 else ''}")
                if similar_cities:
                    print(f"[UYARI] Benzer şehirler: {similar_cities}")
                
                # Benzer şehir önerisi yap
                if similar_cities:
                    raise HTTPException(
                        status_code=400,
                        detail=f"'{city}' şehri bulunamadı. Benzer şehirler: {similar_cities[:3]}"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"'{city}' şehri bulunamadı. Mevcut şehirler: {available_cities[:5]}..."
                    )
            else:
                out = filtered_out

        if start:
            start_date = pd.to_datetime(start).strftime("%Y-%m-%d")
            out = out[out["donem"] >= start_date]
            print(f"[FILTRE] Başlangıç tarihi: {start} -> {len(out)} kayıt")
            
        if end:
            end_date = pd.to_datetime(end).strftime("%Y-%m-%d")
            out = out[out["donem"] <= end_date]
            print(f"[FILTRE] Bitiş tarihi: {end} -> {len(out)} kayıt")

        # İSTATİSTİKLER
        total_records = len(out)
        anomaly_count = out["anomali"].sum()
        anomaly_ratio = anomaly_count / total_records if total_records > 0 else 0
        
        print("=" * 60)
        print(f"[SONUÇ] Kategori: {category.upper()}")
        print(f"[SONUÇ] Şehir: {city if city else 'TÜM ŞEHİRLER'}")
        print(f"[SONUÇ] Toplam kayıt: {total_records}")
        print(f"[SONUÇ] Anomali sayısı: {anomaly_count}")
        print(f"[SONUÇ] Anomali oranı: %{anomaly_ratio*100:.1f}")
        print(f"[SONUÇ] Tolerans: %{tolerance_pct*100:.1f}")
        
        if total_records == 0:
            print("[UYARI] Hiç kayıt kalmadı! Filtreleri kontrol edin.")
        
        # İlk birkaç anomaliyi göster
        anomalies_df = out[out['anomali']]
        if len(anomalies_df) > 0:
            print(f"[ANOMALI] {len(anomalies_df)} anomali bulundu:")
            for i, row in anomalies_df.head(3).iterrows():
                print(f"  📍 {row['sehir']} - {row['donem']}: Gerçek: {row['gercek']:.0f}, Sapma: %{row['dev_pct']*100:.1f}")
        else:
            print("[UYARI] Hiç anomali bulunamadı!")
        print("=" * 60)

        # Sonuçları döndür
        result = [AnomalyItem(**rec) for rec in out.to_dict(orient="records")]
        
        # Debug modunda ekstra bilgi
        if debug:
            debug_info = {
                "category": category,
                "city": city,
                "total_processed": min_len,
                "after_filters": len(out),
                "anomalies_found": anomaly_count,
                "anomaly_ratio": f"{anomaly_ratio*100:.1f}%",
                "tolerance_pct": tolerance_pct,
                "available_cities_sample": sorted(df_test[CITY_COL].unique().tolist())[:10] if CITY_COL in df_test.columns else [],
                "date_range": {
                    "min": out["donem"].min() if len(out) > 0 else None,
                    "max": out["donem"].max() if len(out) > 0 else None
                }
            }
            
            # Debug modu için özel response
            from fastapi.responses import JSONResponse
            return JSONResponse({
                "data": [item.dict() for item in result],
                "debug_info": debug_info
            })
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Anomali tespiti sırasında hata: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/debug/city/{city_name}")
def debug_city_data(city_name: str):
    """Belirli bir şehrin verilerini kontrol et"""
    try:
        # Tüm kategorilerde bu şehri ara
        results = {}
        
        for category, target_col in CONSUMPTION_CATEGORIES.items():
            try:
                df_train, df_test = get_processed_frames(target_col=target_col)
                
                # Büyük/küçük harf duyarsız arama
                city_upper = city_name.upper()
                
                # Şehri bul
                in_train = city_upper in [city.upper() for city in df_train[CITY_COL].dropna().unique()] if CITY_COL in df_train.columns else False
                in_test = city_upper in [city.upper() for city in df_test[CITY_COL].dropna().unique()] if CITY_COL in df_test.columns else False
                
                # Eğer test'te varsa, veri sayılarını al
                test_records = 0
                train_records = 0
                test_dates = []
                target_values = []
                
                if in_test and CITY_COL in df_test.columns:
                    test_data = df_test[df_test[CITY_COL].str.upper() == city_upper]
                    test_records = len(test_data)
                    if DATE_COL in test_data.columns:
                        test_dates = test_data[DATE_COL].dt.strftime('%Y-%m-%d').unique().tolist()
                    if target_col in test_data.columns:
                        target_values = test_data[target_col].tolist()
                
                if in_train and CITY_COL in df_train.columns:
                    train_data = df_train[df_train[CITY_COL].str.upper() == city_upper]
                    train_records = len(train_data)
                
                results[category] = {
                    "in_train": in_train,
                    "in_test": in_test,
                    "test_records": test_records,
                    "train_records": train_records,
                    "test_dates": test_dates[:5],  # İlk 5 tarih
                    "target_values_sample": target_values[:5]  # İlk 5 değer
                }
                    
            except Exception as e:
                results[category] = {"error": str(e)}
        
        # Tüm kategorilerde toplam
        total_test_records = sum(r["test_records"] for r in results.values() if isinstance(r, dict) and "test_records" in r)
        total_train_records = sum(r["train_records"] for r in results.values() if isinstance(r, dict) and "train_records" in r)
        
        return {
            "searched_city": city_name,
            "city_upper": city_name.upper(),
            "summary": {
                "total_test_records": total_test_records,
                "total_train_records": total_train_records,
                "categories_with_data": [cat for cat, res in results.items() if isinstance(res, dict) and res.get("test_records", 0) > 0]
            },
            "results": results
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/all_cities")
def debug_all_cities():
    """Tüm şehirleri ve kayıt sayılarını listele"""
    try:
        df_train, df_test = get_processed_frames(target_col="Genel_Toplam_MWh")
        
        # Test verisindeki şehirler ve kayıt sayıları
        test_city_counts = df_test[CITY_COL].value_counts().to_dict()
        train_city_counts = df_train[CITY_COL].value_counts().to_dict()
        
        # Tüm şehirleri büyük harf yaparak birleştir
        all_cities = sorted(set(df_test[CITY_COL].dropna().unique()))
        
        city_details = {}
        for city in all_cities:
            city_details[city] = {
                "test_records": test_city_counts.get(city, 0),
                "train_records": train_city_counts.get(city, 0),
                "in_both": city in test_city_counts and city in train_city_counts
            }
        
        return {
            "total_cities": len(all_cities),
            "cities": all_cities,
            "city_details": city_details,
            "summary": {
                "cities_with_0_test_records": [city for city, details in city_details.items() if details["test_records"] == 0],
                "cities_with_1_plus_test_records": [city for city, details in city_details.items() if details["test_records"] > 0],
                "max_records_city": max(city_details.items(), key=lambda x: x[1]["test_records"]) if city_details else None
            }
        }
    except Exception as e:
        return {"error": str(e)}

