# anomaly_router.py
# -*- coding: utf-8 -*-
"""
ElektrAize Anomaly Router - FastAPI Router olarak yapılandırılmış
"""
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from fastapi import APIRouter, Query, HTTPException, Depends, Path
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestRegressor
from redis_manager import (
    set_cache, get_cache, generate_cache_key, get_cache_ttl,
    get_cache_stats, invalidate_anomaly_cache, invalidate_scenario_cache
)
import json
import warnings
warnings.filterwarnings('ignore')

from veri_cek import save_model_result
from supabase_init import supabase
from datetime import datetime
from firebase_auth import get_current_user
from veri_cek import (
    get_train_test,         
    get_processed_frames,   
    DATE_COL, CITY_COL
)
from logging_config import get_logger

# Logger oluştur
logger = get_logger(__name__)

# Router oluştur
router = APIRouter(
    prefix="/api/anomalies",
    tags=["Anomaly Detection"],
    responses={
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error"}
    }
)

# -----------------------------------------------------------------------------
# Data Modeller
# -----------------------------------------------------------------------------
class AnomalyItem(BaseModel):
    """Anomali tespit sonucu için veri modeli"""
    sehir: str = Field(..., description="Şehir adı (BÜYÜK HARF, İngilizce karakterler)", example="ISTANBUL")
    donem: str = Field(..., description="Dönem bilgisi (YYYY-MM-DD formatında)", example="2024-01-15")
    gercek: float = Field(..., description="Gerçek enerji tüketimi değeri (MWh)", example=12345.67)
    tahmin: float = Field(..., description="Model tarafından tahmin edilen değer (MWh)", example=12000.0)
    residual: float = Field(..., description="Tahmin hatası (gercek - tahmin)", example=345.67)
    anomali: bool = Field(..., description="Anomali tespit edildi mi?", example=True)
    baseline: Optional[float] = Field(None, description="Mevsimsel baseline değeri (MWh)", example=11500.0)
    dev_pct: Optional[float] = Field(None, description="Baseline'dan sapma yüzdesi", example=0.0735)
    alt_limit: Optional[float] = Field(None, description="Anomali alt limit değeri (MWh)", example=10350.0)
    ust_limit: Optional[float] = Field(None, description="Anomali üst limit değeri (MWh)", example=12650.0)
    category: Optional[str] = Field(None, description="Tüketim kategorisi", example="mesken")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sehir": "ISTANBUL",
                "donem": "2024-01-15",
                "gercek": 12345.67,
                "tahmin": 12000.0,
                "residual": 345.67,
                "anomali": True,
                "baseline": 11500.0,
                "dev_pct": 0.0735,
                "alt_limit": 10350.0,
                "ust_limit": 12650.0,
                "category": "mesken"
            }
        }

class ScenarioRequest(BaseModel):
    """Senaryo analizi için request modeli"""
    category: str = Field(
        ..., 
        description="Tüketim kategorisi",
        example="mesken",
        pattern="^(genel|aydinlatma|mesken|sanayi|tarimsal|ticarethane|diger)$"
    )
    city: str = Field(
        ..., 
        description="Şehir adı (BÜYÜK HARF, İngilizce karakterler)",
        example="ISTANBUL"
    )
    periods: List[str] = Field(
        ..., 
        description="Analiz edilecek tarih listesi (YYYY-MM veya YYYY-MM-DD formatında)",
        example=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        min_items=1,
        max_items=12
    )
    tolerance_pct: float = Field(
        0.10, 
        description="Anomali tespiti için tolerans yüzdesi (0.0 - 1.0 arası)",
        example=0.10,
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "mesken",
                "city": "ISTANBUL",
                "periods": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
                "tolerance_pct": 0.10
            }
        }

class ScenarioItem(BaseModel):
    """Senaryo tablosu için item modeli"""
    donem: str = Field(..., description="Dönem bilgisi (YYYY-MM-DD)", example="2024-01-01")
    gercek: float = Field(..., description="Gerçek tüketim değeri (MWh)", example=12345.67)
    tahmin: float = Field(..., description="Tahmin edilen değer (MWh)", example=12000.0)
    baseline: float = Field(..., description="Baseline değeri (MWh)", example=11500.0)
    anomali: bool = Field(..., description="Anomali tespit edildi mi?", example=True)
    dev_pct: float = Field(..., description="Sapma yüzdesi", example=0.0735)
    residual: float = Field(..., description="Tahmin hatası", example=345.67)
    alt_limit: float = Field(..., description="Alt limit (MWh)", example=10350.0)
    ust_limit: float = Field(..., description="Üst limit (MWh)", example=12650.0)
    risk_level: str = Field(..., description="Risk seviyesi", example="high", pattern="^(low|medium|high)$")

class ScenarioResponse(BaseModel):
    """Senaryo analizi response modeli"""
    category: str = Field(..., description="Kullanılan kategori", example="mesken")
    city: str = Field(..., description="Analiz edilen şehir", example="ISTANBUL")
    periods_requested: List[str] = Field(..., description="İstenen tarihler", example=["2024-01", "2024-02"])
    periods_found: List[str] = Field(..., description="Bulunan tarihler", example=["2024-01-01", "2024-02-01"])
    total_periods: int = Field(..., description="Toplam analiz edilen dönem sayısı", example=5)
    anomaly_count: int = Field(..., description="Tespit edilen anomali sayısı", example=2)
    anomaly_ratio: float = Field(..., description="Anomali oranı (0.0 - 1.0)", example=0.4)
    scenarios: List[ScenarioItem] = Field(..., description="Her dönem için detaylı senaryo bilgileri")
    summary: Dict[str, Any] = Field(..., description="Özet istatistikler (anomaly_percentage, risk_distribution, vb.)")

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
    
    logger.info("Model yükleme işlemi başlatılıyor")
    
    for category_name, target_col in CONSUMPTION_CATEGORIES.items():
        try:
            logger.info(f"{category_name} kategorisi için model yükleniyor (target: {target_col})")
            
            # Veri kontrolü
            Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
            logger.debug(f"{category_name} - Veri boyutları: Xtr={Xtr.shape}, Xte={Xte.shape}")
            
            if len(Xtr) == 0 or len(Xte) == 0:
                logger.warning(f"{category_name} için yeterli veri yok, atlanıyor")
                MODELS[category_name] = None
                continue
            
            logger.debug(f"{category_name} - RandomForest modeli oluşturuluyor")
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
            
            logger.info(f"{category_name} modeli yüklendi - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
            
            # Model sonucunu Supabase'e kaydet
            try:
                save_model_result(
                    model_name=category_name,
                    target=target_col,
                    train_score=train_score,
                    test_score=test_score
                )
                logger.debug(f"{category_name} model sonucu Supabase'e kaydedildi")
            except Exception as e:
                logger.warning(f"{category_name} sonucu DB'ye kaydedilemedi: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"{category_name} modeli yüklenemedi: {str(e)}", exc_info=True)
            MODELS[category_name] = None
    
    loaded_count = sum(1 for m in MODELS.values() if m is not None)
    logger.info(f"Model yükleme tamamlandı: {loaded_count}/{len(CONSUMPTION_CATEGORIES)} model yüklendi")

# -----------------------------------------------------------------------------
# ANOMALİ TESPİTİ
# -----------------------------------------------------------------------------
def detect_anomalies(gercek: pd.Series, baseline: pd.Series, tolerance_pct: float = 0.10):
    """Geliştirilmiş anomali tespiti"""
    baseline_safe = baseline.replace(0, 1e-8)
    alt_limit = baseline_safe * (1 - tolerance_pct)
    ust_limit = baseline_safe * (1 + tolerance_pct)
    anomalies = ((gercek < alt_limit) | (gercek > ust_limit)) & baseline.notna()
    return anomalies, alt_limit, ust_limit

# -----------------------------------------------------------------------------
# ENDPOINT'LER
# -----------------------------------------------------------------------------
@router.get("/health")
def anomalies_health():
    """Anomali servisi sağlık kontrolü"""
    loaded_count = sum(1 for m in MODELS.values() if m is not None)
    return {
        "status": "ok" if loaded_count > 0 else "error",
        "loaded_models": loaded_count,
        "total_categories": len(CONSUMPTION_CATEGORIES),
        "available_categories": [cat for cat, model in MODELS.items() if model is not None]
    }

@router.get(
    "/categories",
    summary="Kategorileri Listele",
    description="Tüm tüketim kategorilerini ve model durumlarını listeler",
    response_description="Kategori listesi ve model yükleme durumları"
)
def get_categories():
    """
    Tüm kategorileri listele
    
    Her kategori için:
    - Model yüklenmiş mi?
    - Model performans metrikleri (R² scores)
    - Target column bilgisi
    """
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

@router.get(
    "",
    response_model=List[AnomalyItem],
    summary="Anomali Tespiti",
    description="""
    Enerji tüketimi anomali tespiti yapar.
    
    **Özellikler:**
    - Kategori bazlı analiz (mesken, aydınlanma, sanayi, vb.)
    - Şehir bazlı filtreleme
    - Tarih aralığı seçimi
    - Redis cache desteği (popüler şehirler için optimize edilmiş)
    - Firebase Authentication gerekli
    
    **Kullanım:**
    - Kategori seçimi zorunlu (varsayılan: genel)
    - Şehir seçimi opsiyonel (belirtilmezse tüm şehirler)
    - Tarih aralığı opsiyonel
    """,
    response_description="Anomali tespit sonuçları listesi"
)
async def get_anomalies(
    category: str = Query(
        "genel", 
        description="Tüketim kategorisi",
        example="mesken",
        pattern="^(genel|aydinlatma|mesken|sanayi|tarimsal|ticarethane|diger)$"
    ),
    city: Optional[str] = Query(
        None, 
        description="Şehir adı (BÜYÜK HARF ve İngilizce karakterlerle, örn: ISTANBUL, ANKARA)",
        example="ISTANBUL"
    ),
    start: Optional[str] = Query(
        None, 
        description="Başlangıç tarihi (YYYY-MM-DD formatında)",
        example="2024-01-01"
    ),
    end: Optional[str] = Query(
        None, 
        description="Bitiş tarihi (YYYY-MM-DD formatında)",
        example="2024-12-31"
    ),
    tolerance_pct: float = Query(
        0.10, 
        description="Anomali tespiti için tolerans yüzdesi (0.0 - 1.0 arası, varsayılan: 0.10 = %10)",
        example=0.10,
        ge=0.0,
        le=1.0
    ),
    debug: bool = Query(
        False, 
        description="Debug modu - ek bilgileri response'a ekler",
        example=False
    ),
    current_user: Dict = Depends(get_current_user)
):
    """
    Geliştirilmiş anomali tespiti endpoint'i.
    
    Seçilen kategori, şehir ve tarih aralığı için anomali analizi yapar.
    Sonuçlar Redis cache'de saklanır (popüler şehirler için 1 saat, diğerleri için 30 dakika).
    """
    try:
        # Kategori adını temizle
        category = category.strip().lower()
        
        # Şehir adını normalize et
        if city:
            city = city.strip().upper()
        
        logger.info(f"Anomali isteği - Kategori: {category}, Şehir: {city or 'TÜM'}, User: {current_user.get('email', 'unknown')}")
        
        # Cache key oluştur
        cache_key = generate_cache_key(
            "anomaly",
            category=category,
            city=city or "all",
            start=start or "all",
            end=end or "all",
            tolerance=tolerance_pct
        )
        
        # Cache'den oku
        cached_result = await get_cache(cache_key)
        if cached_result and not debug:
            logger.info(f"Anomali sonuçları cache'den döndürülüyor (key: {cache_key})")
            return [AnomalyItem(**item) for item in cached_result]
        
        logger.debug(f"Cache miss - Anomali hesaplaması yapılıyor (key: {cache_key})")
        
        # Model kontrolü
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
                    detail="Hiçbir model yüklenmemiş. Backend başlatılırken modeller yüklenmeye çalışıldı ama başarısız oldu. Lütfen backend loglarını kontrol edin."
                )
            raise HTTPException(
                status_code=400, 
                detail=f"'{category}' kategorisi için model yüklenmemiş. Yüklenen kategoriler: {available_cats}"
            )
        
        model_info = MODELS[category]
        target_col = model_info['target_col']
        model = model_info['model']
        
        logger.debug(f"{category} modeli kullanılıyor - Target: {target_col}")

        # Verileri yükle
        logger.debug("Veri çerçeveleri yükleniyor")
        df_train, df_test = get_processed_frames(target_col=target_col)
        Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
        
        logger.debug(f"Veri boyutları - Train: {df_train.shape}, Test: {df_test.shape}")
        if debug:
            if CITY_COL in df_test.columns:
                cities_in_test = df_test[CITY_COL].unique()
                logger.debug(f"Test verisindeki şehir sayısı: {len(cities_in_test)}")
                if city:
                    city_data = df_test[df_test[CITY_COL] == city]
                    logger.debug(f"{city} şehri için kayıt sayısı: {len(city_data)}")

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

        # Supabase'e kaydet
        try:
            y_val = float(np.array(yhat).ravel()[0])
            data = {
                "prediction": y_val,
                "created_at": datetime.now().isoformat(),
            }
            supabase.table("model_results").insert(data).execute()
            logger.debug("Model tahmini Supabase'e kaydedildi")
        except Exception as e:
            logger.warning(f"Supabase'e kayıt yapılamadı: {e}", exc_info=True)

        # Verileri hazırla
        df_test_reset = df_test.reset_index(drop=True)
        min_len = min(len(df_test_reset), len(yte), len(yhat))
        
        df_test_ordered = df_test_reset.head(min_len).copy()
        yte_series = pd.Series(yte.values[:min_len])
        yhat_series = pd.Series(yhat[:min_len])
        baseline_series = df_test_ordered["baseline"].reset_index(drop=True)

        logger.debug(f"{category} - {min_len} kayıt işlendi")

        # Anomali tespiti
        logger.debug(f"Anomali tespiti yapılıyor (tolerance: {tolerance_pct})")
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

        # Filtreleme
        if city:
            if city == "ISTANBUL":
                city_mask = out["sehir"].isin(["ISTANBUL-ASYA", "ISTANBUL-AVRUPA"])
                filtered_out = out[city_mask].copy()
                filtered_out["sehir"] = "ISTANBUL"
                out = filtered_out
            else:
                city_mask = out["sehir"] == city
                if city_mask.sum() == 0:
                    available_cities = sorted(out["sehir"].unique()) if len(out) > 0 else []
                    raise HTTPException(
                        status_code=400,
                        detail=f"'{city}' şehri bulunamadı. Mevcut şehirler: {available_cities[:5]}..."
                    )
                out = out[city_mask]

        if start:
            start_date = pd.to_datetime(start).strftime("%Y-%m-%d")
            out = out[out["donem"] >= start_date]
            
        if end:
            end_date = pd.to_datetime(end).strftime("%Y-%m-%d")
            out = out[out["donem"] <= end_date]

        # İstatistikler
        total_records = len(out)
        anomaly_count = out["anomali"].sum()
        anomaly_ratio = anomaly_count / total_records if total_records > 0 else 0
        
        logger.info(f"Anomali analizi tamamlandı - Kategori: {category.upper()}, Şehir: {city if city else 'TÜM'}, "
                   f"Toplam: {total_records}, Anomali: {anomaly_count} (%{anomaly_ratio*100:.1f})")

        # Sonuçları hazırla
        result = [AnomalyItem(**rec) for rec in out.to_dict(orient="records")]
        
        # Cache'e kaydet (debug modunda cache'leme)
        if not debug:
            result_dict = [item.dict() for item in result]
            await set_cache(cache_key, result_dict, city=city)
            logger.debug(f"Anomali sonuçları cache'lendi (key: {cache_key})")
        
        if debug:
            from fastapi.responses import JSONResponse
            debug_info = {
                "category": category,
                "city": city,
                "total_processed": min_len,
                "after_filters": len(out),
                "anomalies_found": anomaly_count,
                "anomaly_ratio": f"{anomaly_ratio*100:.1f}%",
                "cache_key": cache_key,
                "cache_ttl": get_cache_ttl(city)
            }
            return JSONResponse({
                "data": [item.dict() for item in result],
                "debug_info": debug_info
            })
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        # Generic exception handler yakalayacak, burada sadece log
        logger.error(f"Anomali tespiti sırasında beklenmeyen hata: {str(e)}", exc_info=True)
        raise  # Global handler'a bırak

@router.get(
    "/debug/city/{city_name}",
    summary="Şehir Veri Kontrolü (Debug)",
    description="Belirli bir şehrin tüm kategorilerdeki veri durumunu kontrol eder (debug amaçlı)",
    tags=["Debug"],
    deprecated=True
)
def debug_city_data(
    city_name: str = Path(..., description="Kontrol edilecek şehir adı", example="ISTANBUL"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Belirli bir şehrin verilerini kontrol et (debug endpoint).
    
    Bu endpoint şehrin hangi kategorilerde veriye sahip olduğunu gösterir.
    Production'da kullanılmamalıdır.
    """
    try:
        results = {}
        for category, target_col in CONSUMPTION_CATEGORIES.items():
            try:
                df_train, df_test = get_processed_frames(target_col=target_col)
                city_upper = city_name.upper()
                
                in_train = city_upper in [city.upper() for city in df_train[CITY_COL].dropna().unique()] if CITY_COL in df_train.columns else False
                in_test = city_upper in [city.upper() for city in df_test[CITY_COL].dropna().unique()] if CITY_COL in df_test.columns else False
                
                test_records = len(df_test[df_test[CITY_COL].str.upper() == city_upper]) if in_test and CITY_COL in df_test.columns else 0
                train_records = len(df_train[df_train[CITY_COL].str.upper() == city_upper]) if in_train and CITY_COL in df_train.columns else 0
                
                results[category] = {
                    "in_train": in_train,
                    "in_test": in_test,
                    "test_records": test_records,
                    "train_records": train_records,
                }
            except Exception as e:
                results[category] = {"error": str(e)}
        
        return {
            "searched_city": city_name,
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}

@router.post(
    "/scenarios",
    response_model=ScenarioResponse,
    summary="Anomali Senaryosu Analizi",
    description="""
    Tarih aralığı seçimi ile detaylı anomali senaryosu analizi.
    
    **Özellikler:**
    - Birden fazla tarih seçimi (örn: 5 ay)
    - Her dönem için detaylı analiz
    - Risk seviyesi hesaplama (low/medium/high)
    - Özet istatistikler
    - Redis cache desteği
    
    **Kullanım:**
    - Kategori ve şehir seçimi zorunlu
    - En az 1, en fazla 12 tarih seçilebilir
    - Tarih formatı: YYYY-MM veya YYYY-MM-DD
    """,
    response_description="Seçilen dönemler için detaylı anomali senaryosu"
)
async def get_scenarios(
    request: ScenarioRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Tarih aralığı seçimi ile anomali senaryosu analizi.
    
    Kullanıcı kategori, şehir ve birden fazla tarih seçebilir.
    Seçilen tarihler için detaylı anomali senaryosu döndürülür.
    Her dönem için risk seviyesi ve özet istatistikler hesaplanır.
    """
    try:
        category = request.category.strip().lower()
        city = request.city.strip().upper()
        periods = [p.strip() for p in request.periods]
        tolerance_pct = request.tolerance_pct
        
        logger.info(f"Senaryo isteği - Kategori: {category}, Şehir: {city}, Tarih sayısı: {len(periods)}, "
                   f"User: {current_user.get('email', 'unknown')}")
        
        # Cache key oluştur
        periods_str = "_".join(sorted(periods))
        cache_key = generate_cache_key(
            "scenario",
            category=category,
            city=city,
            periods=periods_str,
            tolerance=tolerance_pct
        )
        
        # Cache'den oku
        cached_result = await get_cache(cache_key)
        if cached_result:
            logger.info(f"Senaryo sonuçları cache'den döndürülüyor (key: {cache_key})")
            return ScenarioResponse(**cached_result)
        
        logger.debug(f"Cache miss - Senaryo hesaplaması yapılıyor (key: {cache_key})")
        
        # Model kontrolü
        if category not in CONSUMPTION_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"'{category}' kategorisi bulunamadı. Mevcut kategoriler: {list(CONSUMPTION_CATEGORIES.keys())}"
            )
        
        if category not in MODELS or MODELS[category] is None:
            available_cats = [cat for cat, model in MODELS.items() if model is not None]
            raise HTTPException(
                status_code=400,
                detail=f"'{category}' kategorisi için model yüklenmemiş. Yüklenen kategoriler: {available_cats}"
            )
        
        # Tarih formatını normalize et (YYYY-MM veya YYYY-MM-DD)
        normalized_periods = []
        for period in periods:
            try:
                # YYYY-MM formatını YYYY-MM-01'e çevir
                if len(period) == 7 and period[4] == '-':
                    period = f"{period}-01"
                pd.to_datetime(period)  # Validasyon
                normalized_periods.append(period)
            except:
                raise HTTPException(
                    status_code=400,
                    detail=f"Geçersiz tarih formatı: '{period}'. Format: YYYY-MM veya YYYY-MM-DD"
                )
        
        if not normalized_periods:
            raise HTTPException(
                status_code=400,
                detail="En az bir geçerli tarih belirtmelisiniz."
            )
        
        model_info = MODELS[category]
        target_col = model_info['target_col']
        model = model_info['model']
        
        # Verileri yükle
        df_train, df_test = get_processed_frames(target_col=target_col)
        Xtr, Xte, ytr, yte = get_train_test(target_col=target_col)
        
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
        
        # Verileri hazırla
        df_test_reset = df_test.reset_index(drop=True)
        min_len = min(len(df_test_reset), len(yte), len(yhat))
        
        df_test_ordered = df_test_reset.head(min_len).copy()
        yte_series = pd.Series(yte.values[:min_len])
        yhat_series = pd.Series(yhat[:min_len])
        baseline_series = df_test_ordered["baseline"].reset_index(drop=True)
        
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
        })
        
        # Şehir filtresi
        if city == "ISTANBUL":
            city_mask = out["sehir"].isin(["ISTANBUL-ASYA", "ISTANBUL-AVRUPA"])
            filtered_out = out[city_mask].copy()
            filtered_out["sehir"] = "ISTANBUL"
            out = filtered_out
        else:
            city_mask = out["sehir"] == city
            if city_mask.sum() == 0:
                available_cities = sorted(out["sehir"].unique()) if len(out) > 0 else []
                raise HTTPException(
                    status_code=400,
                    detail=f"'{city}' şehri bulunamadı. Mevcut şehirler: {available_cities[:5]}..."
                )
            out = out[city_mask]
        
        # Tarih filtresi - seçilen tarihler için
        out[DATE_COL] = pd.to_datetime(out["donem"])
        
        # Normalize edilmiş tarihleri datetime'a çevir
        period_dates = []
        for period in normalized_periods:
            try:
                if len(period) == 7:  # YYYY-MM
                    period_dates.append(pd.to_datetime(f"{period}-01"))
                else:  # YYYY-MM-DD
                    period_dates.append(pd.to_datetime(period))
            except:
                continue
        
        if not period_dates:
            raise HTTPException(
                status_code=400,
                detail="Geçerli tarih bulunamadı."
            )
        
        # Seçilen tarihler için filtrele (ay bazında)
        period_mask = pd.Series([False] * len(out))
        for period_date in period_dates:
            # Aynı ay ve yıl için eşleş
            mask = (out[DATE_COL].dt.year == period_date.year) & (out[DATE_COL].dt.month == period_date.month)
            period_mask = period_mask | mask
        
        out = out[period_mask].copy()
        
        if len(out) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Seçilen tarihler için '{city}' şehrinde veri bulunamadı."
            )
        
        # Risk seviyesi hesapla
        def calculate_risk_level(dev_pct: float, anomali: bool) -> str:
            if not anomali:
                return "low"
            abs_dev = abs(dev_pct)
            if abs_dev > 0.20:  # %20'den fazla sapma
                return "high"
            elif abs_dev > 0.15:  # %15-20 arası
                return "medium"
            else:
                return "low"
        
        # Senaryo item'larını oluştur
        scenarios = []
        periods_found = sorted(out["donem"].unique().tolist())
        
        for _, row in out.iterrows():
            scenarios.append(ScenarioItem(
                donem=row["donem"],
                gercek=round(row["gercek"], 2),
                tahmin=round(row["tahmin"], 2),
                baseline=round(row["baseline"], 2),
                anomali=bool(row["anomali"]),
                dev_pct=round(row["dev_pct"], 4),
                residual=round(row["residual"], 2),
                alt_limit=round(row["alt_limit"], 2),
                ust_limit=round(row["ust_limit"], 2),
                risk_level=calculate_risk_level(row["dev_pct"], row["anomali"])
            ))
        
        # Özet istatistikler
        anomaly_count = out["anomali"].sum()
        total_periods = len(out)
        anomaly_ratio = anomaly_count / total_periods if total_periods > 0 else 0
        
        avg_deviation = out["dev_pct"].abs().mean()
        max_deviation = out["dev_pct"].abs().max()
        
        summary = {
            "total_periods_analyzed": total_periods,
            "anomaly_count": int(anomaly_count),
            "anomaly_ratio": round(anomaly_ratio, 4),
            "anomaly_percentage": round(anomaly_ratio * 100, 2),
            "average_deviation": round(avg_deviation, 4),
            "max_deviation": round(max_deviation, 4),
            "risk_distribution": {
                "high": sum(1 for s in scenarios if s.risk_level == "high"),
                "medium": sum(1 for s in scenarios if s.risk_level == "medium"),
                "low": sum(1 for s in scenarios if s.risk_level == "low")
            }
        }
        
        logger.info(f"Senaryo analizi tamamlandı - Kategori: {category.upper()}, Şehir: {city}, "
                   f"İstenen tarihler: {len(normalized_periods)}, Bulunan: {len(periods_found)}, "
                   f"Anomali: {anomaly_count}/{total_periods} (%{anomaly_ratio*100:.1f})")
        
        response = ScenarioResponse(
            category=category,
            city=city,
            periods_requested=normalized_periods,
            periods_found=periods_found,
            total_periods=total_periods,
            anomaly_count=int(anomaly_count),
            anomaly_ratio=round(anomaly_ratio, 4),
            scenarios=scenarios,
            summary=summary
        )
        
        # Cache'e kaydet
        await set_cache(cache_key, response.dict(), city=city)
        logger.debug(f"Senaryo sonuçları cache'lendi (key: {cache_key})")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Generic exception handler yakalayacak, burada sadece log
        logger.error(f"Senaryo analizi sırasında beklenmeyen hata: {str(e)}", exc_info=True)
        raise  # Global handler'a bırak

@router.get(
    "/cache/stats",
    summary="Cache İstatistikleri",
    description="Redis cache performans istatistiklerini döndürür (hit rate, miss count, vb.)",
    tags=["System", "Cache"]
)
async def get_cache_statistics(current_user: Dict = Depends(get_current_user)):
    """
    Cache istatistiklerini döndür.
    
    Returns:
        - hits: Cache hit sayısı
        - misses: Cache miss sayısı
        - sets: Cache kayıt sayısı
        - errors: Hata sayısı
        - hit_rate: Hit oranı (%)
        - total_requests: Toplam istek sayısı
    """
    stats = await get_cache_stats()
    return stats

@router.post(
    "/cache/invalidate",
    summary="Cache Temizleme",
    description="Belirtilen kriterlere göre cache'i temizler (admin işlemi)",
    tags=["System", "Cache"]
)
async def invalidate_cache(
    category: Optional[str] = Query(None, description="Temizlenecek kategori", example="mesken"),
    city: Optional[str] = Query(None, description="Temizlenecek şehir", example="ISTANBUL"),
    cache_type: str = Query(
        "anomaly", 
        description="Cache tipi",
        example="anomaly",
        pattern="^(anomaly|scenario)$"
    ),
    current_user: Dict = Depends(get_current_user)
):
    """
    Cache'i invalidate et (admin işlemi).
    
    Seçilen kategori, şehir ve cache tipine göre cache'leri temizler.
    """
    if cache_type == "anomaly":
        deleted = await invalidate_anomaly_cache(category, city)
    elif cache_type == "scenario":
        deleted = await invalidate_scenario_cache(category, city)
    else:
        raise HTTPException(status_code=400, detail="cache_type 'anomaly' veya 'scenario' olmalı")
    
    return {
        "message": f"{cache_type} cache invalidate edildi",
        "deleted_keys": deleted,
        "category": category,
        "city": city
    }

@router.get(
    "/cache-test",
    summary="Cache Test",
    description="Redis cache bağlantısını test eder",
    tags=["System", "Cache", "Debug"],
    deprecated=True
)
async def cache_test(current_user: Dict = Depends(get_current_user)):
    """
    Cache test endpoint (debug amaçlı).
    
    Redis cache'in çalışıp çalışmadığını test eder.
    """
    key = "test_key"
    value = "ElektrAize FastAPI test başarılı! 🚀"
    await set_cache(key, value)
    result = await get_cache(key)
    return {"key": key, "value": result}

