import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client
from pathlib import Path

print("Program basladi...")

# --- .env dosyasini oku ---
script_dir = Path(__file__).resolve().parent
env_path = script_dir / "bubir.env" 
loaded = load_dotenv(env_path)
if loaded:
    print(" bubir.env bulundu ve yuklendi")
else:
    print(f" HATA: '{env_path}' bulunamadi!")
    exit() 

# --- Supabase degiskenlerini al ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print(" HATA: SUPABASE_URL veya SUPABASE_ANON_KEY eksik.")
    exit()

# --- Supabase client olustur ---
print("Supabase client olusturuluyor...")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
print(" Supabase client basariyla olusturuldu")

# --- Tablolari cek ---
tablolar = ["genel_elektrik", "weather", "nufus", "hizmet", "train_2022_2023", "test_2024_2025"]
dfs = {}

for tablo in tablolar:
    print(f"'{tablo}' tablosu cekiliyor...")
    try:
        response = supabase.table(tablo).select("*").execute()
        dfs[tablo] = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        print(f" '{tablo}' tablosu cekildi. Satir x Sutun:", dfs[tablo].shape)
    except Exception as e:
        print(f" '{tablo}' cekilirken hata:", e)
        dfs[tablo] = pd.DataFrame()

# --- DataFrame'leri degiskenlere ata ---
df_genel = dfs.get("genel_elektrik", pd.DataFrame())
df_weather = dfs.get("weather", pd.DataFrame())
df_nufus = dfs.get("nufus", pd.DataFrame())
df_hizmet = dfs.get("hizmet", pd.DataFrame())
df_train = dfs.get("train_2022_2023", pd.DataFrame())
df_test = dfs.get("test_2024_2025", pd.DataFrame())

print(" Tum tablolar cekildi.")

# --- Merge islemleri (sadece Donem ile) ---
df_train_merged = df_train.merge(df_weather, on="Donem", how="left") \
                          .merge(df_nufus, on="Donem", how="left") \
                          .merge(df_hizmet, on="Donem", how="left")
df_test_merged = df_test.merge(df_weather, on="Donem", how="left") \
                        .merge(df_nufus, on="Donem", how="left") \
                        .merge(df_hizmet, on="Donem", how="left")

print(" Merge tamamlandi:")
print("Train:", df_train_merged.shape)
print("Test :", df_test_merged.shape)

# --- Train/Test hazirlama fonksiyonu ---
def get_train_test(target_col="Genel_Toplam_MWh"):
    # Temiz sütunları filtrele
    temiz_cols = ["Temiz_Aydinlatma","Temiz_Mesken","Temiz_Sanayi",
                  "Temiz_Tarımsal","Temiz_Ticarethane","Temiz_Diger",
                  "Temiz_Genel","Temiz"]

    # Temiz olmayan satırları cikar
    df_train_clean = df_train_merged[df_train_merged["Temiz"]==True]
    df_test_clean = df_test_merged[df_test_merged["Temiz"]==True]

    # Sayısal sütunları al, temiz sütunlarını düş
    drop_cols = [c for c in temiz_cols if c in df_train_clean.columns]
    X_train = df_train_clean.select_dtypes(include=["number"]).drop(columns=drop_cols, errors="ignore")
    y_train = df_train_clean[target_col]

    X_test = df_test_clean.select_dtypes(include=["number"]).drop(columns=drop_cols, errors="ignore")
    y_test = df_test_clean[target_col]

    return X_train, X_test, y_train, y_test
