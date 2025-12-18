import sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
from supabase_init import supabase

try:
    print("Checking date range for 'test_2024_2025'...")
    # Fetch all dates (lightweight)
    res = supabase.table('test_2024_2025').select("Donem").execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        df['Donem'] = pd.to_datetime(df['Donem'])
        min_date = df['Donem'].min()
        max_date = df['Donem'].max()
        print(f"✅ 'test_2024_2025' Date Range:")
        print(f"   Min: {min_date}")
        print(f"   Max: {max_date}")
        print(f"   Total rows: {len(df)}")
    else:
        print("⚠️ Table 'test_2024_2025' is empty or not found.")

except Exception as e:
    print(f"❌ Error: {e}")
