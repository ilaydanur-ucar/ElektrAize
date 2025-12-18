import asyncio
import os
import json
import sys
from datetime import datetime

# ... (imports)

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
sys.stdout = Tee('db_report.txt', 'w')

# ---------------------------------------------------------
# 1. Supabase Verification
# ---------------------------------------------------------
async def verify_supabase():
    print("\n" + "="*50)
    print("SUPABASE VERIFICATION")
    print("="*50)
    try:
        from supabase_init import supabase
        
        # Try to basic health check or get user info if possible, or list a known table
        # Attempt to get data from 'model_results' which was seen in code
        print("Attempting to fetch last 5 entries from 'model_results'...")
        response = supabase.table('model_results').select("*").limit(5).order('created_at', desc=True).execute()
        
        if hasattr(response, 'data') and response.data:
            print(f"✅ Successfully fetched {len(response.data)} rows:")
            print(json.dumps(response.data, indent=2, default=str))
        else:
            print("⚠️ Connected, but table 'model_results' might be empty or not accessible.")
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"❌ Supabase Error: {e}")

# ---------------------------------------------------------
# 2. Firebase Verification
# ---------------------------------------------------------
async def verify_firebase():
    print("\n" + "="*50)
    print("FIREBASE VERIFICATION")
    print("="*50)
    try:
        from firebase_init import db
        
        if db is None:
            print("❌ Firebase client is not initialized (check configuration).")
            return

        # List collections
        print("Attempting to list collections (first 5)...")
        collections = db.collections()
        count = 0
        for collection in collections:
            print(f"\n📂 Collection: {collection.id}")
            # Get first 5 documents from the collection
            docs = collection.limit(5).stream()
            doc_list = []
            for doc in docs:
                doc_list.append(doc.to_dict())
            
            if doc_list:
                print(f"  ✅ First {len(doc_list)} documents:")
                print(json.dumps(doc_list, indent=2, default=str))
            else:
                print("  ⚠️ Collection is empty.")
            
            count += 1
            if count >= 3: # Limit to checking first 3 collections to avoid huge output
                print("... (stopping after 3 collections)")
                break
                
        if count == 0:
             print("⚠️ No collections found or unable to list them.")

    except Exception as e:
        print(f"❌ Firebase Error: {e}")

# ---------------------------------------------------------
# 3. Redis Verification
# ---------------------------------------------------------
async def verify_redis():
    print("\n" + "="*50)
    print("REDIS VERIFICATION")
    print("="*50)
    try:
        from redis_manager import redis_client
        
        pong = await redis_client.ping()
        if pong:
            print("✅ Redis PING Successful")
            
            # Get some keys
            keys = await redis_client.keys("*")
            print(f"Total Keys Found: {len(keys)}")
            
            # Show first 5 keys and their values
            for key in keys[:5]:
                key_type = await redis_client.type(key)
                value = None
                if key_type == 'string':
                    value = await redis_client.get(key)
                else:
                    value = f"[{key_type} type - content hidden]"
                
                print(f"🔑 Key: {key}")
                print(f"   Value: {value}")
        else:
             print("❌ Redis PING Failed")

    except Exception as e:
        print(f"❌ Redis Error: {e}")

# ---------------------------------------------------------
# Main Execution
# ---------------------------------------------------------
async def main():
    print("Starting verification of all databases...")
    await verify_supabase()
    await verify_firebase()
    await verify_redis()
    print("\n" + "="*50)
    print("VERIFICATION COMPLETE")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
