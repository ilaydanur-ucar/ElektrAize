# -*- coding: utf-8 -*-
# Kullanım:
#   python anomaly_pipeline.py --input data/raw/energy_weather.csv --city Malatya
# veya tüm şehirler:
#   python anomaly_pipeline.py --input data/raw/energy_weather.csv --all

import os, argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
import joblib

# ==== CONFIG ====
DATE_COL  = "Donem"               # tarih (YYYY-MM, YYYY-MM-DD)
CITY_COL  = "Sehir"               # il adı
TARGET    = "Genel_Toplam_MWh"    # tahmin edilecek sütun
USE_XGB   = True                  # False yaparsan RandomForest kullanır
LAGS      = [1, 2, 3, 12]
REPORTS   = Path("reports"); REPORTS.mkdir(exist_ok=True, parents=True)
MODELS    = Path("models");  MODELS.mkdir(exist_ok=True, parents=True)

# ----------------- Yardımcılar -----------------
def ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    return df

def basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    # sayısal kolonları dönüştür
    for c in df.columns:
        if c == TARGET or c.endswith("_MWh"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # sıralama
    df = df.sort_values([CITY_COL, DATE_COL])
    return df

def impute_city_month(df: pd.DataFrame) -> pd.DataFrame:
    """Eksik değerleri öncelikle şehir+ay ortalamasıyla doldur.
       Sonra şehir ortalaması, en son genel ortalama fallback."""
    df = df.copy()
    df["month"] = df[DATE_COL].dt.month

    # sadece sayısal kolonlarda doldurma yapacağız
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if TARGET not in num_cols:
        num_cols.append(TARGET)

    for col in num_cols:
        # şehir+ay ortalaması
        df[col] = df[col].fillna(df.groupby([CITY_COL, "month"])[col].transform("mean"))
        # şehir ortalaması
        df[col] = df[col].fillna(df.groupby(CITY_COL)[col].transform("mean"))
        # genel ortalama
        df[col] = df[col].fillna(df[col].mean())

    return df

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year"]  = df[DATE_COL].dt.year
    df["month"] = df[DATE_COL].dt.month
    # lag/rolling
    df = df.sort_values([CITY_COL, DATE_COL])
    for lag in LAGS:
        df[f"{TARGET}_lag{lag}"] = df.groupby(CITY_COL)[TARGET].shift(lag)
    df[f"{TARGET}_roll3"]  = df.groupby(CITY_COL)[TARGET].rolling(3).mean().reset_index(0, drop=True)
    df[f"{TARGET}_roll12"] = df.groupby(CITY_COL)[TARGET].rolling(12).mean().reset_index(0, drop=True)
    return df

def feature_cols(df: pd.DataFrame):
    drop_cols = {TARGET, DATE_COL, CITY_COL}
    return [c for c in df.columns if c not in drop_cols and df[c].dtype != "O"]

def train_city(df: pd.DataFrame, city: str) -> str:
    g = df[df[CITY_COL] == city].dropna(subset=[TARGET]).copy()
    # yeterli veri kontrolü
    if g.shape[0] < 24:
        raise ValueError(f"{city}: Eğitim için veri çok az ({g.shape[0]})")

    X = g[feature_cols(g)]
    y = g[TARGET]

    if USE_XGB:
        model = XGBRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1,
            tree_method="hist"
        )
    else:
        model = RandomForestRegressor(
            n_estimators=400,
            random_state=42,
            n_jobs=-1
        )

    model.fit(X, y)
    path = MODELS / f"{'xgb' if USE_XGB else 'rf'}_{city}.pkl"
    joblib.dump(model, path)
    return str(path)

def predict_and_residuals(df: pd.DataFrame, city: str, model_path: str) -> pd.DataFrame:
    g = df[df[CITY_COL] == city].copy()
    model = joblib.load(model_path)
    X = g[feature_cols(g)].fillna(method="ffill").fillna(method="bfill")  # güvenlik
    g["yhat"] = model.predict(X)
    g["residual"] = g[TARGET] - g["yhat"]
    return g

def mad_anomaly_flags(residuals: pd.Series, thr: float = 3.5) -> pd.Series:
    med = np.median(residuals)
    mad = np.median(np.abs(residuals - med))
    if mad == 0 or np.isnan(mad):
        return pd.Series([False] * len(residuals), index=residuals.index)
    robust_z = 0.6745 * (residuals - med) / mad
    return np.abs(robust_z) > thr

# ----------------- Ana akış -----------------
def run_for_city(df: pd.DataFrame, city: str, thr: float = 3.5) -> pd.DataFrame:
    model_path = train_city(df, city)
    g = predict_and_residuals(df, city, model_path)
    flags = mad_anomaly_flags(g["residual"], thr=thr)
    anomalies = g.loc[flags, [CITY_COL, DATE_COL, TARGET, "yhat", "residual"]]
    return anomalies.sort_values(DATE_COL)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Birleşik CSV (enerji + hava + vs.)")
    ap.add_argument("--city", help="Tek bir şehir ismi")
    ap.add_argument("--all", action="store_true", help="Tüm şehirler için çalıştır")
    ap.add_argument("--thr", type=float, default=3.5, help="MAD eşiği (default 3.5)")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df = ensure_datetime(df)
    df = basic_clean(df)
    df = impute_city_month(df)
    df = add_features(df)

    if args.all:
        cities = sorted(df[CITY_COL].dropna().unique().tolist())
    else:
        if not args.city:
            raise SystemExit("Şehir belirt veya --all kullan.")
        cities = [args.city]

    all_out = []
    for c in cities:
        try:
            out = run_for_city(df, c, thr=args.thr)
            print(f"[{c}] anomalies: {len(out)}")
            all_out.append(out)
        except Exception as e:
            print(f"[{c}] SKIP: {e}")

    if all_out:
        result = pd.concat(all_out, ignore_index=True).sort_values([CITY_COL, DATE_COL])
        out_path = REPORTS / ("anomalies_all.csv" if args.all else f"anomalies_{cities[0]}.csv")
        result.to_csv(out_path, index=False)
        print(f"✔ kaydedildi -> {out_path}")
    else:
        print("Uyarı: hiç anomali bulunamadı ya da veri yok.")

if __name__ == "__main__":
    main()
