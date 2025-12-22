# -*- coding: utf-8 -*-
"""
veri_cek.py - Optimize Edilmiş Versiyon
- Daha hızlı ve güvenli veri işleme
- Daha iyi hata yönetimi
- Performans iyileştirmeleri
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from typing import Dict, Tuple, Optional
import logging

# ===================== KONFİGÜRASYON =====================
DATE_COL = "Donem"
CITY_COL = "Sehir"
TARGET = "Genel_Toplam_MWh"
LAGS = [1, 2, 3, 12]

# Tablo konfigürasyonu
TABLES = {
    "genel": "genel_elektrik",
    "weather": "weather", 
    "nufus": "nufus",
    "hizmet": "hizmet",
    "train": "train_2022_2023",
    "test": "test_2024_2025",
}

# Logging setup - logging_config.py'den merkezi logger kullan
from logging_config import get_logger
logger = get_logger(__name__)

# ===================== OPTIMIZE YARDIMCILAR =====================
def _to_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Daha hızlı datetime dönüşümü"""
    if DATE_COL not in df.columns:
        return df.copy()
    
    df = df.copy()
    # Daha hızlı datetime parsing
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce', infer_datetime_format=True)
    return df

def _numericize(df: pd.DataFrame) -> pd.DataFrame:
    """Tüm sayısal kolonları optimize şekilde dönüştür"""
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number, 'object']).columns
    
    for col in numeric_cols:
        if col not in [DATE_COL, CITY_COL]:
            # Sadece gerçekten sayısal olması gereken kolonları dönüştür
            if col == TARGET or col.endswith(('_MWh', '_lag', '_roll', 'sayi', 'deger', 'oran')):
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def _smart_merge(left: pd.DataFrame, right: pd.DataFrame, how: str = "left") -> pd.DataFrame:
    """Daha optimize merge işlemi"""
    if left.empty:
        return right.copy()
    if right.empty:
        return left.copy()
        
    left = _to_datetime(left.copy())
    right = _to_datetime(right.copy())

    # Merge key'lerini belirle
    merge_keys = [DATE_COL]
    if CITY_COL in left.columns and CITY_COL in right.columns:
        merge_keys.append(CITY_COL)
    
    # Gereksiz kolonları temizle (hız için)
    common_cols = set(left.columns).intersection(set(right.columns)) - set(merge_keys)
    if common_cols:
        right = right.drop(columns=common_cols, errors='ignore')
    
    return left.merge(right, on=merge_keys, how=how, suffixes=('', '_right'))

def impute_city_month(df: pd.DataFrame) -> pd.DataFrame:
    """Daha hızlı eksik veri doldurma"""
    if df.empty:
        return df
        
    df = _numericize(_to_datetime(df.copy()))
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        return df

    # Ay bilgisini ekle
    if DATE_COL in df.columns:
        df["month"] = df[DATE_COL].dt.month

    # Grup bazlı doldurma - daha optimize
    if CITY_COL in df.columns and "month" in df.columns:
        for col in numeric_cols:
            # Şehir+ay bazında doldur
            city_month_mean = df.groupby([CITY_COL, "month"])[col].transform("mean")
            df[col] = df[col].fillna(city_month_mean)
            
            # Şehir bazında doldur
            city_mean = df.groupby(CITY_COL)[col].transform("mean")
            df[col] = df[col].fillna(city_mean)
    
    # Genel ortalama ile doldur
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].mean())
    
    return df

def add_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    """Hava durumu verilerinden özellikler çıkar"""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Hava durumu kolonlarını bul (genel pattern'ler) - Donem hariç
    # Hava durumu kolonlarını bul - Donem (tarih) ve diğer tarih kolonlarını kesinlikle hariç tut
    weather_cols = []
    excluded_date_cols = {DATE_COL, 'Donem', 'Tarih', 'Date', 'date'}
    
    for col in df.columns:
        # Tarih kolonlarını atla
        if col in excluded_date_cols:
            continue
        # Tarih tipinde olan kolonları atla
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue
        # Sadece sayısal kolonlar
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        # Keyword kontrolü
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in 
               ['temp', 'sicaklik', 'temperature', 'humidity', 'yagis', 'rain', 
                'ruzgar', 'wind', 'basinc', 'pressure', 'gunes', 'sun', 'bulut', 'cloud']):
            weather_cols.append(col)
    
    if not weather_cols:
        logger.debug("Hava durumu kolonları bulunamadı")
        return df
    
    logger.info(f"{len(weather_cols)} hava durumu kolonu bulundu: {weather_cols[:5]}...")
    
    # Şehir bazında sıralama
    if CITY_COL in df.columns and DATE_COL in df.columns:
        df = df.sort_values([CITY_COL, DATE_COL]).reset_index(drop=True)
        
        for col in weather_cols:
            # Tarih kolonunu kesinlikle atla
            if col == DATE_COL or col == 'Donem':
                continue
            # Sadece sayısal kolonlar ve tarih tipinde olmayanlar
            if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
                # Lag features (geçmiş hava durumu)
                for lag in [1, 2, 3]:
                    df[f"{col}_lag{lag}"] = df.groupby(CITY_COL)[col].shift(lag)
                
                # Rolling mean (ortalama hava durumu)
                df[f"{col}_roll3"] = df.groupby(CITY_COL)[col].rolling(3, min_periods=1).mean().reset_index(level=0, drop=True)
                df[f"{col}_roll12"] = df.groupby(CITY_COL)[col].rolling(12, min_periods=1).mean().reset_index(level=0, drop=True)
                
                # Mevsimsel ortalamalar (ay bazında)
                if "month" in df.columns:
                    df[f"{col}_monthly_avg"] = df.groupby([CITY_COL, "month"])[col].transform("mean")
    
    return df

def add_population_features(df: pd.DataFrame) -> pd.DataFrame:
    """Nüfus verilerinden özellikler çıkar"""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Nüfus kolonlarını bul
    pop_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                ['nufus', 'population', 'pop', 'kisi', 'insan', 'sayi'])]
    
    if not pop_cols:
        logger.debug("Nüfus kolonları bulunamadı")
        return df
    
    logger.info(f"{len(pop_cols)} nüfus kolonu bulundu: {pop_cols[:5]}...")
    
    # Şehir bazında sıralama
    if CITY_COL in df.columns and DATE_COL in df.columns:
        df = df.sort_values([CITY_COL, DATE_COL]).reset_index(drop=True)
        
        for col in pop_cols:
            if df[col].dtype in [np.number, 'float64', 'int64']:
                # Nüfus değişim oranı (yıllık büyüme)
                df[f"{col}_change"] = df.groupby(CITY_COL)[col].pct_change()
                df[f"{col}_change_12"] = df.groupby(CITY_COL)[col].pct_change(12)  # Yıllık değişim
                
                # Nüfus trendi (rolling mean)
                df[f"{col}_roll12"] = df.groupby(CITY_COL)[col].rolling(12, min_periods=1).mean().reset_index(level=0, drop=True)
                
                # Enerji tüketimi başına nüfus (eğer target varsa)
                if TARGET in df.columns:
                    df[f"energy_per_capita"] = df[TARGET] / (df[col] + 1e-8)  # Sıfıra bölme hatası önleme
    
    return df

def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Hava ve nüfus verileri arasındaki etkileşim özellikleri"""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Tarih ve zaman kolonlarını hariç tut
    excluded_cols = {DATE_COL, 'Donem', 'Tarih', 'Date', 'date', 'month', 'year', 'quarter', 'day_of_year'}
    
    # Hava durumu kolonları - sadece sayısal, tarih olmayan
    weather_cols = []
    for col in df.columns:
        if col in excluded_cols:
            continue
        # Tarih tipinde olan kolonları kesinlikle atla
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue
        # Sadece sayısal kolonlar
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        # Keyword kontrolü - 'donem' içinde 'nem' geçiyor, bu yüzden özel kontrol
        col_lower = col.lower()
        if 'donem' in col_lower:
            continue  # Donem kolonunu kesinlikle atla
        if any(keyword in col_lower for keyword in ['temp', 'sicaklik', 'temperature', 'humidity']):
            weather_cols.append(col)
    
    # Nüfus kolonları - sadece sayısal ve tarih olmayan
    pop_cols = []
    for col in df.columns:
        if col in excluded_cols:
            continue
        if df[col].dtype not in [np.number, 'float64', 'int64', 'float32', 'int32']:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue
        if any(keyword in col.lower() for keyword in ['nufus', 'population', 'pop']):
            pop_cols.append(col)
    
    # Etkileşim feature'ları
    if weather_cols and pop_cols:
        # Sıcaklık * Nüfus (soğutma/heating ihtiyacı)
        temp_col = weather_cols[0] if weather_cols else None
        pop_col = pop_cols[0] if pop_cols else None
        
        if temp_col and pop_col:
            # Donem veya tarih kolonları kesinlikle atlanmalı
            if temp_col in {DATE_COL, 'Donem'} or pop_col in {DATE_COL, 'Donem'}:
                logger.warning(f"temp_pop_interaction eklenemedi: Tarih kolonu seçildi ({temp_col}, {pop_col})")
            else:
                try:
                    # Kolonların sayısal olduğunu ve tarih tipinde olmadığını kontrol et
                    if (pd.api.types.is_numeric_dtype(df[temp_col]) and 
                        pd.api.types.is_numeric_dtype(df[pop_col]) and
                        not pd.api.types.is_datetime64_any_dtype(df[temp_col]) and 
                        not pd.api.types.is_datetime64_any_dtype(df[pop_col])):
                        # Sayısal değerlere dönüştür ve çarp
                        temp_vals = pd.to_numeric(df[temp_col], errors='coerce')
                        pop_vals = pd.to_numeric(df[pop_col], errors='coerce')
                        df["temp_pop_interaction"] = temp_vals * pop_vals
                        logger.debug(f"temp_pop_interaction eklendi: {temp_col} * {pop_col}")
                    else:
                        logger.warning(f"temp_pop_interaction eklenemedi: Kolonlardan biri tarih tipinde veya sayısal değil ({temp_col}, {pop_col})")
                except Exception as e:
                    logger.warning(f"temp_pop_interaction eklenemedi: {e}", exc_info=True)
    
    # Mevsimsel etkileşimler
    if "month" in df.columns and weather_cols:
        temp_col = weather_cols[0] if weather_cols else None
        if temp_col:
            try:
                # Mevsimsel sıcaklık etkisi
                df["seasonal_temp"] = df.groupby("month")[temp_col].transform("mean")
                logger.debug(f"seasonal_temp eklendi: {temp_col}")
            except Exception as e:
                logger.warning(f"seasonal_temp eklenemedi: {e}")
    
    return df

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize zaman bazlı özellikler + Hava/Nüfus feature'ları"""
    if df.empty:
        return df
        
    df = _to_datetime(df.copy())
    
    # Temel zaman özellikleri
    if DATE_COL in df.columns:
        df["year"] = df[DATE_COL].dt.year
        df["month"] = df[DATE_COL].dt.month
        df["quarter"] = df[DATE_COL].dt.quarter
        df["day_of_year"] = df[DATE_COL].dt.dayofyear
        df["is_summer"] = df["month"].isin([6, 7, 8]).astype(int)
        df["is_winter"] = df["month"].isin([12, 1, 2]).astype(int)

    # Lag ve rolling features - sadece şehir bazında
    if CITY_COL in df.columns and DATE_COL in df.columns:
        df = df.sort_values([CITY_COL, DATE_COL]).reset_index(drop=True)
        
        # Target lag features (sadece target varsa)
        if TARGET in df.columns:
            for lag in LAGS:
                df[f"{TARGET}_lag{lag}"] = df.groupby(CITY_COL)[TARGET].shift(lag)
            
            # Rolling features - daha hızlı hesaplama
            rolling_3 = df.groupby(CITY_COL)[TARGET].rolling(3, min_periods=1).mean()
            rolling_12 = df.groupby(CITY_COL)[TARGET].rolling(12, min_periods=1).mean()
            
            df[f"{TARGET}_roll3"] = rolling_3.reset_index(level=0, drop=True)
            df[f"{TARGET}_roll12"] = rolling_12.reset_index(level=0, drop=True)
    
    # Hava durumu feature'ları ekle
    df = add_weather_features(df)
    
    # Nüfus feature'ları ekle
    df = add_population_features(df)
    
    # Etkileşim feature'ları ekle
    df = add_interaction_features(df)
    
    return df

def finalize_xy(train_df: pd.DataFrame, test_df: pd.DataFrame, target_col: str = TARGET) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Optimize feature seçimi ve hazırlığı"""
    
    # Ortak sayısal kolonları bul
    num_train = train_df.select_dtypes(include=[np.number])
    num_test = test_df.select_dtypes(include=[np.number])
    
    common_cols = sorted(set(num_train.columns).intersection(set(num_test.columns)))
    
    # Target'ı emin olarak ekle
    if target_col not in common_cols and target_col in train_df.columns:
        common_cols.append(target_col)
    
    # Gereksiz kolonları temizle
    exclude_patterns = ['_right', 'index', 'level_0']
    common_cols = [col for col in common_cols if not any(pattern in str(col) for pattern in exclude_patterns)]
    
    # Feature ve target'ları ayır
    X_train = train_df[common_cols].drop(columns=[target_col], errors='ignore')
    X_test = test_df[common_cols].drop(columns=[target_col], errors='ignore')
    
    y_train = pd.to_numeric(train_df[target_col], errors='coerce')
    y_test = pd.to_numeric(test_df[target_col], errors='coerce')
    
    # NaN değerleri optimize doldur
    X_train = X_train.fillna(X_train.mean(numeric_only=True))
    X_test = X_test.fillna(X_test.mean(numeric_only=True))
    
    y_train = y_train.fillna(y_train.mean())
    y_test = y_test.fillna(y_test.mean())
    
    return X_train, X_test, y_train, y_test

def _to_bool_series(s: pd.Series) -> pd.Series:
    """Daha güvenli boolean dönüşümü"""
    if s.empty:
        return pd.Series([], dtype=bool)
    
    # Mevcut boolean değerleri koru
    if s.dtype == bool:
        return s
    
    # String/numara dönüşümü
    return s.astype(str).str.lower().isin(["1", "true", "t", "yes", "y", "evet"])

# ===================== VERİ ÇEKME =====================
class SupabaseManager:
    """Supabase bağlantı yöneticisi"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Bağlantıyı başlat - supabase_init.py'den import edilen client'ı kullan"""
        # supabase_init.py'den zaten oluşturulmuş client'ı kullan
        from supabase_init import supabase
        
        if supabase is None:
            raise EnvironmentError(
                "Supabase client oluşturulamadı. "
                ".env dosyasında SUPABASE_URL ve SUPABASE_ANON_KEY kontrol edin."
            )
        
        self.client = supabase
        logger.info("Supabase bağlantısı başarılı (SupabaseManager).")

    
    def fetch_table(self, table_name: str) -> pd.DataFrame:
        """Tek bir tablo çek (Pagination ile tüm veriyi al)"""
        try:
            all_data = []
            offset = 0
            limit = 1000 # Supabase max limit per request
            
            while True:
                # Range queries are inclusive: [start, end]
                res = self.client.table(table_name)\
                    .select("*")\
                    .range(offset, offset + limit - 1)\
                    .execute()
                
                rows = res.data
                if not rows:
                    break
                    
                all_data.extend(rows)
                
                # If we got fewer rows than limit, we've reached the end
                if len(rows) < limit:
                    break
                    
                offset += limit
                
            return pd.DataFrame(all_data) if all_data else pd.DataFrame()
            
        except Exception as e:
            logger.error(f"{table_name} çekilemedi: {e}")
            return pd.DataFrame()

# ===================== GLOBAL CACHE =====================
_DATA_CACHE = {}

def clear_cache():
    """Cache'i temizle"""
    global _DATA_CACHE
    _DATA_CACHE = {}
    logger.info("Veri cache temizlendi.")

def fetch_tables(use_cache: bool = True) -> Dict[str, pd.DataFrame]:
    """Tüm tabloları paralel olarak çek (optimize + cache)"""
    global _DATA_CACHE
    
    if use_cache and _DATA_CACHE:
        # Basit kontrol: Önemli tablolar dolu mu?
        if (not _DATA_CACHE.get("nufus", pd.DataFrame()).empty and 
            not _DATA_CACHE.get("hizmet", pd.DataFrame()).empty and 
            not _DATA_CACHE.get("weather", pd.DataFrame()).empty):
             logger.info("Tablolar cache'den alındı.")
             return _DATA_CACHE.copy()
    
    sb = SupabaseManager()
    dfs = {}
    
    for nick, table in TABLES.items():
        try:
            # Eğer cache'de varsa ve boş değilse koru (partial update durumunda)
            if use_cache and nick in _DATA_CACHE and not _DATA_CACHE[nick].empty:
                dfs[nick] = _DATA_CACHE[nick]
                continue

            df = sb.fetch_table(table)
            dfs[nick] = df
            logger.info(f"{table} tablosu yüklendi -> {df.shape}")
        except Exception as e:
            logger.warning(f"{table} tablosu çekilemedi: {e}", exc_info=True)
            # Cache'de varsa eskisini kullan, yoksa boş
            dfs[nick] = _DATA_CACHE.get(nick, pd.DataFrame())
            
    # Cache güncelle
    if use_cache:
        _DATA_CACHE = dfs
        
    return dfs

# ===================== ANA PIPELINE =====================
def build_train_test_frames(dfs: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Optimize merge pipeline"""
    train = dfs.get("train", pd.DataFrame()).copy()
    test = dfs.get("test", pd.DataFrame()).copy()
    
    if train.empty or test.empty:
        logger.error("Train veya test verisi boş!")
        return train, test

    # Yardımcı tablolar
    weather = dfs.get("weather", pd.DataFrame())
    nufus = dfs.get("nufus", pd.DataFrame())
    hizmet = dfs.get("hizmet", pd.DataFrame())

    # Sıralı merge - daha optimize
    for right_df, name in [(weather, "weather"), (nufus, "nufus"), (hizmet, "hizmet")]:
        if not right_df.empty:
            train = _smart_merge(train, right_df)
            test = _smart_merge(test, right_df)
            logger.debug(f"{name} tablosu merge edildi")

    logger.info(f"Merge bitti -> Train: {train.shape}, Test: {test.shape}")
    return train, test

def get_processed_data(target_col: str = TARGET, return_frames: bool = False):
    """
    Ana veri işleme pipeline'ı
    """
    try:
        # Veriyi çek
        dfs = fetch_tables()
        df_train, df_test = build_train_test_frames(dfs)
        
        if df_train.empty or df_test.empty:
            raise ValueError("Eğitim veya test verisi boş!")
        
        # Temizlik filtresi
        for df in [df_train, df_test]:
            if "Temiz" in df.columns:
                df = df[_to_bool_series(df["Temiz"])]
        
        # Özellik mühendisliği
        df_train = add_time_features(impute_city_month(df_train))
        df_test = add_time_features(impute_city_month(df_test))
        
        if return_frames:
            return df_train, df_test
        else:
            return finalize_xy(df_train, df_test, target_col)
            
    except Exception as e:
        logger.error(f"Veri işleme hatası: {e}")
        raise

def get_train_test(target_col: str = TARGET):
    """Model için X,y train/test döndür"""
    return get_processed_data(target_col, return_frames=False)

def get_processed_frames(target_col: str = TARGET):
    """İşlenmiş DataFrame'ler döndür"""
    return get_processed_data(target_col, return_frames=True)

# ===================== TEST =====================
if __name__ == "__main__":
    logger.info("Optimize veri pipeline testi başlatılıyor...")
    
    try:
        X_tr, X_te, y_tr, y_te = get_train_test()
        logger.info(f"✓ X_train: {X_tr.shape}, X_test: {X_te.shape}")
        logger.debug(f"✓ Özellikler: {list(X_tr.columns)[:8]}...")
        logger.debug(f"✓ Target örnek: {y_tr.head(3).tolist()}")
        
        # İşlenmiş frame'leri de test et
        df_tr, df_te = get_processed_frames()
        logger.info(f"✓ İşlenmiş Train: {df_tr.shape}, Test: {df_te.shape}")
        logger.info("✓ Tüm testler başarılı!")
        
    except Exception as e:
        logger.error(f"✗ Test hatası: {e}", exc_info=True)
        # ===================== MODEL SONUÇLARINI DB'YE YAZ =====================
def save_model_result(model_name: str, target: str, train_score: float, test_score: float):
    """
    Model sonuçlarını Supabase'e kaydeder.
    """
    from datetime import datetime
    sb = SupabaseManager()

    data = {
        "model_name": model_name,
        "target_column": target,
        "train_r2": round(train_score, 3),
        "test_r2": round(test_score, 3),
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        res = sb.client.table("model_results").insert(data).execute()
        if hasattr(res, "data") and res.data:
            logger.debug(f"Model sonucu kaydedildi: {model_name} ({target})")
        else:
            logger.warning(f"Model sonucu eklenemedi: {res}")
    except Exception as e:
        logger.error(f"Model sonucu kayıt hatası: {model_name} - {e}", exc_info=True)
