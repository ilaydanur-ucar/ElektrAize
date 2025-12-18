import asyncio
import os
import json
import sys
from datetime import datetime

# Redirect stdout to a file to ensure we capture everything
class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode, encoding='utf-8')
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()

# Start logging to file
sys.stdout = Tee('reverify_report.txt', 'w')
sys.stderr = sys.stdout # Redirect stderr too

async def main():
    print("STARTING RE-VERIFICATION")
    print("="*50)
    
    # 1. Supabase Verification (Should pass or at least show empty list)
    try:
        from supabase_init import supabase
        print("Checking 'model_results' table (expecting success but maybe 0 rows)...")
        # Now filtering by created_at should work if we insert correctly, OR we just list without sort
        # Let's simple list
        response = supabase.table('model_results').select("*").limit(5).execute()
        if hasattr(response, 'data'):
            print(f"✅ Supabase 'model_results' accessible. Rows: {len(response.data)}")
            if response.data:
                 print(json.dumps(response.data[0], indent=2, default=str))
        else:
            print("⚠️ Supabase returned no data object.")
    except Exception as e:
        print(f"❌ Supabase Error: {e}")

    # 2. Redis Check (Optional, just logging)
    try:
        from redis_manager import redis_client
        pong = await redis_client.ping()
        print(f"Redis status: {'✅ UP' if pong else '❌ DOWN'}")
    except Exception as e:
         print(f"Redis status: ❌ DOWN ({e})")

    print("="*50)
    print("COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())
