# anomaly_router.py
# -*- coding: utf-8 -*-
"""
ElektrAize Anomaly Router - Adapted from anomaly_api.py
"""
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sklearn.ensemble import RandomForestRegressor
from redis_manager import set_cache, get_cache
import asyncio
import warnings
warnings.filterwarnings('ignore')
#--sena---
from veri_cek import save_model_result
from supabase_init import supabase
from datetime import datetime
#----sena--
from firebase_auth import get_current_user
from typing import Dict

from veri_cek import (
    get_train_test,         
    get_processed_frames,   
    DATE_COL, CITY_COL
)

# -----------------------------------------------------------------------------
# Router Setup
# -----------------------------------------------------------------------------
router = APIRouter(tags=["Anomalies"])

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
    
# Tüm tüketim kategorileri
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
# MODEL YÜKLEME
# -----------------------------------------------------------------------------
def load_all_models():
    """Tüm kategoriler için model yükle"""
    global MODELS
    
    for category_name, target_col in CONSUMPTION_CATEGORIES.items():
        try:
            print(f"\n[MODEL] {category_name} için model yükleniyor...")
            Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
            
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
            
            train_score = model.score(Xtr, ytr)
            test_score = model.score(Xte, yte) if len(Xte) > 0 else 0
            
            MODELS[category_name] = {
                'model': model,
                'target_col': target_col,
                'train_score': train_score,
                'test_score': test_score
            }
            
            print(f"[OK] {category_name} modeli yüklendi - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
            
            try:
                save_model_result(
                    model_name=category_name,
                    target=target_col,
                    train_score=train_score,
                    test_score=test_score
                )
            except Exception as e:
                print(f"[WARN] {category_name} sonucu DB'ye kaydedilemedi: {e}")
        
        except Exception as e:
            print(f"[ERROR] {category_name} modeli yüklenemedi: {str(e)}")
            MODELS[category_name] = None

# -----------------------------------------------------------------------------
# ANOMALİ TESPİTİ
# -----------------------------------------------------------------------------
def detect_anomalies(gercek: pd.Series, baseline: pd.Series, tolerance_pct: float = 0.10):
    baseline_safe = baseline.replace(0, 1e-8)
    alt_limit = baseline_safe * (1 - tolerance_pct)
    ust_limit = baseline_safe * (1 + tolerance_pct)
    anomalies = ((gercek < alt_limit) | (gercek > ust_limit)) & baseline.notna()
    return anomalies, alt_limit, ust_limit

# -----------------------------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------------------------

@router.get("/categories")
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

@router.get("/anomalies", response_model=List[AnomalyItem])
async def anomalies(
    category: str = Query("genel", description="Tüketim kategorisi"),
    city: Optional[str] = Query(None, description="Şehir adı (BÜYÜK HARF ve İngilizce karakterlerle)"),
    start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD"),
    tolerance_pct: float = Query(0.10, description="Tolerans yüzdesi"),
    debug: bool = Query(False, description="Debug bilgilerini göster"),
):
    try:
        category = category.strip().lower()
        if city:
            city = city.strip().upper()
        
        # Cache key oluştur
        cache_key = f"anomaly:{category}:{city or 'none'}:{start or 'none'}:{end or 'none'}:{tolerance_pct}"
        
        # Cache kontrolü - EN BAŞINDA
        cached_result = await get_cache(cache_key)
        if cached_result is not None:
            print("Redis cache HIT")
            # Cache'den gelen veriyi AnomalyItem listesine çevir
            if isinstance(cached_result, list):
                return [AnomalyItem(**item) if isinstance(item, dict) else item for item in cached_result]
            return cached_result
        
        if category not in CONSUMPTION_CATEGORIES:
            available_cats = list(CONSUMPTION_CATEGORIES.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"'{category}' kategorisi bulunamadı. Mevcut kategoriler: {available_cats}"
            )
        
        if category not in MODELS or MODELS[category] is None:
            available_cats = [cat for cat, model in MODELS.items() if model is not None]
            if len(available_cats) == 0:
                raise HTTPException(
                    status_code=503,
                    detail="Hiçbir model yüklenmemiş. Backend başlatılırken modeller yüklenmeye çalışıldı ama başarısız oldu."
                )
            raise HTTPException(
                status_code=400, 
                detail=f"'{category}' kategorisi için model yüklenmemiş."
            )
        
        model_info = MODELS[category]
        target_col = model_info['target_col']
        model = model_info['model']
        
        df_train, df_test = get_processed_frames(target_col=target_col)
        Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
        
        # Baseline Calculation (Train & Test)
        df_train = df_train.copy()
        df_train["ay"] = pd.to_datetime(df_train[DATE_COL]).dt.month
        seasonal_baseline = (
            df_train.groupby([CITY_COL, "ay"])[target_col]
            .mean()
            .rename("baseline")
            .reset_index()
        )

        # Apply Baseline
        df_train = df_train.merge(seasonal_baseline, on=[CITY_COL, "ay"], how="left")
        df_test = df_test.copy()
        df_test["ay"] = pd.to_datetime(df_test[DATE_COL]).dt.month
        df_test = df_test.merge(seasonal_baseline, on=[CITY_COL, "ay"], how="left")

        # Predictions
        yhat_test = model.predict(Xte)
        yhat_train = model.predict(Xtr)

        # --- Helper to create result DataFrame ---
        def create_result_df(df_orig, y_true_arr, y_pred_arr):
            df_reset = df_orig.reset_index(drop=True)
            min_len = min(len(df_reset), len(y_true_arr), len(y_pred_arr))
            
            df_ordered = df_reset.head(min_len).copy()
            y_true_s = pd.Series(y_true_arr[:min_len].ravel() if hasattr(y_true_arr, 'ravel') else y_true_arr[:min_len]) # Handle series/array
            y_pred_s = pd.Series(y_pred_arr[:min_len])
            baseline_s = df_ordered["baseline"].reset_index(drop=True)

            flags_anom, alt_lim, ust_lim = detect_anomalies(
                y_true_s, baseline_s, tolerance_pct
            )

            return pd.DataFrame({
                "sehir": df_ordered[CITY_COL].astype(str),
                "donem": pd.to_datetime(df_ordered[DATE_COL]).dt.strftime("%Y-%m-%d"),
                "gercek": y_true_s.astype(float),
                "tahmin": y_pred_s.astype(float),
                "residual": (y_true_s - y_pred_s).astype(float),
                "anomali": flags_anom.astype(bool),
                "baseline": baseline_s.astype(float),
                "dev_pct": ((y_true_s - baseline_s) / baseline_s.replace(0, 1e-8)).astype(float),
                "alt_limit": alt_lim.astype(float),
                "ust_limit": ust_lim.astype(float),
                "category": category
            })

        # Process both sets
        # Get y_true values safely (handle series/arrays)
        ytr_val = ytr.values if hasattr(ytr, 'values') else ytr
        yte_val = yte.values if hasattr(yte, 'values') else yte

        out_train = create_result_df(df_train, ytr_val, yhat_train)
        out_test = create_result_df(df_test, yte_val, yhat_test)

        # Combine
        out = pd.concat([out_train, out_test], ignore_index=True)
        out = out.sort_values("donem") # Sort chronological

        # Save latest prediction to Supabase (optional, keeping existing logic)
        # try:
        #     y_val = float(np.array(yhat_test).ravel()[0])
        #     data = {
        #         "prediction": y_val,
        #         "created_at": datetime.now().isoformat(),
        #     }
        #     supabase.table("model_results").insert(data).execute()
        # except Exception as e:
        #     print(f"[WARN] Supabase error: {e}")

        if city:
            if city == "ISTANBUL":
                city_mask = out["sehir"].isin(["ISTANBUL-ASYA", "ISTANBUL-AVRUPA"])
                filtered_out = out[city_mask].copy()
                filtered_out["sehir"] = "ISTANBUL"
                out = filtered_out
            else:
                out = out[out["sehir"] == city]
                
            if len(out) == 0:
                 raise HTTPException(status_code=400, detail=f"'{city}' şehri bulunamadı.")

        if start:
            out = out[out["donem"] >= pd.to_datetime(start).strftime("%Y-%m-%d")]
        if end:
            out = out[out["donem"] <= pd.to_datetime(end).strftime("%Y-%m-%d")]

        result = [AnomalyItem(**rec) for rec in out.to_dict(orient="records")]
        
        # Cache'e kaydet - Hesaplama tamamlandıktan sonra, return edilmeden önce
        result_dict = [item.dict() for item in result]
        await set_cache(cache_key, result_dict, city=city)
        print("Redis cache SET")
        
        if debug:
            from fastapi.responses import JSONResponse
            debug_info = {
                "category": category,
                "count": len(out),
                "city": city
            }
            return JSONResponse({
                "data": [item.dict() for item in result],
                "debug_info": debug_info
            })
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/city/{city_name}")
def debug_city_data(city_name: str):
    """Debug endpoint for city data"""
    try:
        results = {}
        for category, target_col in CONSUMPTION_CATEGORIES.items():
            df_train, df_test = get_processed_frames(target_col=target_col)
            results[category] = {
                "train_records": len(df_train[df_train[CITY_COL].str.upper() == city_name.upper()]) if CITY_COL in df_train.columns else 0,
                "test_records": len(df_test[df_test[CITY_COL].str.upper() == city_name.upper()]) if CITY_COL in df_test.columns else 0
            }
        return {"city": city_name, "results": results}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/all_cities")
def debug_all_cities():
    try:
        df_train, df_test = get_processed_frames(target_col="Genel_Toplam_MWh")
        all_cities = sorted(set(df_test[CITY_COL].dropna().unique()))
        return {"total": len(all_cities), "cities": all_cities}
    except Exception as e:
        return {"error": str(e)}

@router.get("/cache-test")
async def cache_test():
    key = "test_key_router"
    value = "Router Test OK"
    await set_cache(key, value)
    result = await get_cache(key)
    return {"key": key, "value": result}
