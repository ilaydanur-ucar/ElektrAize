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

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize zaman bazlı özellikler"""
    if df.empty or TARGET not in df.columns:
        return df
        
    df = _to_datetime(df.copy())
    
    # Temel zaman özellikleri
    if DATE_COL in df.columns:
        df["year"] = df[DATE_COL].dt.year
        df["month"] = df[DATE_COL].dt.month
        df["quarter"] = df[DATE_COL].dt.quarter

    # Lag ve rolling features - sadece şehir bazında
    if CITY_COL in df.columns and DATE_COL in df.columns:
        df = df.sort_values([CITY_COL, DATE_COL]).reset_index(drop=True)
        
        # Lag features
        for lag in LAGS:
            df[f"{TARGET}_lag{lag}"] = df.groupby(CITY_COL)[TARGET].shift(lag)
        
        # Rolling features - daha hızlı hesaplama
        rolling_3 = df.groupby(CITY_COL)[TARGET].rolling(3, min_periods=1).mean()
        rolling_12 = df.groupby(CITY_COL)[TARGET].rolling(12, min_periods=1).mean()
        
        df[f"{TARGET}_roll3"] = rolling_3.reset_index(level=0, drop=True)
        df[f"{TARGET}_roll12"] = rolling_12.reset_index(level=0, drop=True)
    
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
        """Bağlantıyı başlat"""
        script_dir = Path(__file__).resolve().parent
        env_path = script_dir / "bubir.env"
        
        if not load_dotenv(env_path):
            logger.warning(f"'.env' bulunamadı: {env_path}")
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise EnvironmentError("SUPABASE_URL veya SUPABASE_ANON_KEY eksik.")
        
        self.client = create_client(url, key)
        logger.info("Supabase bağlantısı başarılı")
    
    def fetch_table(self, table_name: str) -> pd.DataFrame:
        """Tek bir tablo çek"""
        try:
            res = self.client.table(table_name).select("*").execute()
            return pd.DataFrame(res.data) if res.data else pd.DataFrame()
        except Exception as e:
            logger.error(f"{table_name} çekilemedi: {e}")
            return pd.DataFrame()

def fetch_tables() -> Dict[str, pd.DataFrame]:
    """Tüm tabloları paralel olarak çek (optimize)"""
    sb = SupabaseManager()
    dfs = {}
    
    for nick, table in TABLES.items():
        try:
            df = sb.fetch_table(table)
            dfs[nick] = df
            logger.info(f"[OK] {table} -> {df.shape}")
        except Exception as e:
            logger.warning(f"[WARN] {table} çekilemedi: {e}")
            dfs[nick] = pd.DataFrame()
    
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
            logger.debug(f"{name} merge edildi")

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
    print("Optimize veri pipeline testi...")
    
    try:
        X_tr, X_te, y_tr, y_te = get_train_test()
        print(f"✓ X_train: {X_tr.shape}, X_test: {X_te.shape}")
        print(f"✓ Özellikler: {list(X_tr.columns)[:8]}...")
        print(f"✓ Target örnek: {y_tr.head(3).tolist()}")
        
        # İşlenmiş frame'leri de test et
        df_tr, df_te = get_processed_frames()
        print(f"✓ İşlenmiş Train: {df_tr.shape}, Test: {df_te.shape}")
        print("✓ Tüm testler başarılı!")
        
    except Exception as e:
        print(f"✗ Hata: {e}")