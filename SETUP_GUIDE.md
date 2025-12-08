# ElektrAize Backend Setup Guide

## Quick Start (From Zero)

Follow these steps to get the ElektrAize backend running on your machine.

---

## Prerequisites

1. **Python 3.10+** installed ([Download](https://www.python.org/downloads/))
2. **Git** installed (optional, for cloning)
3. **Firebase Account** with a project created
4. **Supabase Account** with a project created
5. **Redis Server** (optional, for caching - see installation below)

---

## Step-by-Step Installation

### 1️⃣ Navigate to Project Directory

```powershell
cd c:\Users\ilayd\OneDrive\Desktop\ElektrAize\ElektrAize
```

### 2️⃣ Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Or for CMD:
# .\venv\Scripts\activate.bat
```

### 3️⃣ Install Dependencies

**IMPORTANT**: Use the corrected requirements file that includes all ML libraries:

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install from CORRECTED requirements
pip install -r requirements_CORRECTED.txt
```

### 4️⃣ Configure Environment Variables

Copy the example env file and fill in your credentials:

```powershell
# Copy example to actual .env
copy .env.example .env

# Edit .env with your actual values (use notepad or any text editor)
notepad .env
```

Required values to fill in `.env`:
- `FIREBASE_API_KEY` - From Firebase Console > Project Settings
- `SUPABASE_URL` - From Supabase Dashboard > Settings > API
- `SUPABASE_KEY` - From Supabase Dashboard > Settings > API (anon/public key)

### 5️⃣ Download Firebase Admin Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** (gear icon) → **Service Accounts**
4. Click **Generate New Private Key**
5. Save the downloaded JSON file as `firebase_config.json` in the project root:
   ```
   c:\Users\ilayd\OneDrive\Desktop\ElektrAize\ElektrAize\firebase_config.json
   ```

### 6️⃣ Install Redis (Optional - for Caching)

**Option A: Windows Installer**
- Download from: [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
- Install and run as a service

**Option B: Docker (Recommended)**
```powershell
docker run -d -p 6379:6379 --name elektraize-redis redis
```

**Option C: Skip Redis**
- The app will work without Redis, just without caching benefits
- Comment out Redis-related code in `anomaly_api.py` if needed

### 7️⃣ Verify Installation

Test that all dependencies are installed:

```powershell
# Check Python version
python --version
# Should show 3.10 or higher

# Check installed packages
pip list
# Should show fastapi, firebase-admin, supabase, numpy, pandas, sklearn, etc.

# Verify environment variables loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Firebase API Key:', os.getenv('FIREBASE_API_KEY')[:10] + '...' if os.getenv('FIREBASE_API_KEY') else 'NOT SET')"
```

### 8️⃣ Run the Backend

**Option 1: Run main.py directly**
```powershell
python main.py
```

**Option 2: Run with uvicorn (recommended for development)**
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Run anomaly API separately**
```powershell
uvicorn anomaly_api:app --reload --port 8001
```

### 9️⃣ Test the Backend

Open your browser or use curl:

```powershell
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "service": "ElektrAize Gateway"}

# Test available ML categories
curl http://localhost:8000/categories

# Expected: List of available consumption categories and model status
```

---

## What Was Fixed

The audit found and fixed the following critical issues:

### ✅ Fixed Issues

1. **firebase_init.py** - Hardcoded path to another user's directory
   - **Before**: `C:\Users\Sena Ceylan\OneDrive\Desktop\ElektrAize\firebase_config.json`
   - **After**: Uses environment variable or relative path

2. **test_firebase.py** - Import error (auth not exported)
   - **Before**: `from firebase_init import db, auth`
   - **After**: `from firebase_admin import auth`

3. **redis_manager.py** - Hardcoded Redis connection
   - **Before**: Hard-coded `localhost:6379`
   - **After**: Uses `REDIS_HOST` and `REDIS_PORT` env vars

4. **anomali_pipeline.py** - Deprecated pandas syntax
   - **Before**: `fillna(method="ffill")`
   - **After**: `ffill()` (pandas 2.0+ compatible)

5. **main.py** - Duplicate import
   - **Before**: CORSMiddleware imported twice
   - **After**: Single import

6. **requirements.txt** - Missing ML dependencies
   - **Before**: Missing numpy, pandas, scikit-learn, xgboost
   - **After**: All dependencies included in `requirements_CORRECTED.txt`

---

## Database Architecture

Your backend uses **4 different databases**:

| Database | Purpose | Config |
|----------|---------|--------|
| **Firebase Firestore** | User auth + profiles | `firebase_config.json` |
| **Supabase (PostgreSQL)** | Energy data + ML results | `.env` (SUPABASE_URL/KEY) |
| **SQLite** | Local user storage | `.env` (DATABASE_URL) |
| **Redis** | API caching | `.env` (REDIS_HOST/PORT) |

---

## Troubleshooting

### Issue: "Firebase config not found"
**Solution**: Make sure `firebase_config.json` exists in project root or set `FIREBASE_CONFIG_PATH` in `.env`

### Issue: "Module not found" errors
**Solution**: Make sure you installed from `requirements_CORRECTED.txt`, not the old `requirements.txt`

### Issue: Redis connection errors
**Solution**: Either install Redis or comment out Redis imports in `anomaly_api.py` (lines 13, 560-569)

### Issue: Supabase connection errors
**Solution**: Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env` are correct

### Issue: "No module named 'sklearn'"
**Solution**: 
```powershell
pip install scikit-learn
```

---

## Next Steps

1. **Configure Supabase tables** - Make sure tables exist:
   - `genel_elektrik`
   - `weather`
   - `nufus`
   - `hizmet`
   - `train_2022_2023`
   - `test_2024_2025`
   - `model_results`

2. **Test ML models** - Visit `/categories` to see loaded models

3. **Test authentication** - Try the `/me` endpoint with Firebase token

4. **Deploy** - See deployment guide for production setup

---

## File Checklist

After setup, you should have:
- ✅ `venv/` directory (virtual environment)
- ✅ `.env` file (from `.env.example`)
- ✅ `firebase_config.json` (downloaded from Firebase)
- ✅ All Python packages installed
- ✅ Redis running (optional)

---

**Setup Complete! 🎉**

Your backend should now be running at `http://localhost:8000`

API documentation available at: `http://localhost:8000/docs`
