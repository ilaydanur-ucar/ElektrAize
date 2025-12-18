import sys
import json
# Fix for Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

try:
    from supabase_init import supabase
    # Try to list *tables* not just rows.
    # Supabase-py doesn't have a direct "list_tables" method on the client usually, 
    # but we can try to guess common names or just inspect 'predictions'.
    
    print("Checking for 'predictions' table...")
    response = supabase.table('predictions').select("*").limit(1).execute()
    if hasattr(response, 'data'):
        print("'predictions' table EXISTS.")
        print("Columns:", list(response.data[0].keys()) if response.data else "Empty table")
    else:
        print("'predictions' table check failed.")

except Exception as e:
    print(f"Error checking 'predictions' table: {e}")
