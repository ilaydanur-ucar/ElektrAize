import sys
import json
from supabase_init import supabase

# Fix for Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

def inspect_table():
    print("Inspecting 'model_results' table...")
    try:
        # Fetch just 1 row without strict ordering to see what we get
        response = supabase.table('model_results').select("*").limit(1).execute()
        
        if hasattr(response, 'data') and response.data:
            print("Successfully fetched a row. Keys found:")
            print(list(response.data[0].keys()))
            print("\nFull row data:")
            print(json.dumps(response.data[0], indent=2, default=str))
        else:
            print("Table appears empty or accessible columns are restricted.")
            print(f"Response data: {response.data if hasattr(response, 'data') else 'None'}")
            
    except Exception as e:
        print(f"Error inspecting table: {e}")

if __name__ == "__main__":
    inspect_table()
