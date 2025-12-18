from veri_cek import fetch_tables
import pandas as pd

def check_cities():
    print("Veriler çekiliyor...")
    dfs = fetch_tables()
    
    if "train" in dfs and not dfs["train"].empty:
        cities = dfs["train"]["Sehir"].unique()
        print("\nVeritabanındaki Şehirler (Train):")
        for city in sorted(cities):
            if "CANKIRI" in city or "ÇANKIRI" in city or "AGRI" in city or "AĞRI" in city:
                print(f"-> {city}")
    else:
        print("Train verisi boş!")

if __name__ == "__main__":
    check_cities()
