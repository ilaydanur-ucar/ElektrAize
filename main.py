from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from firebase_auth import get_current_user
from email_service import send_verification_email

# Firebase initialization
from firebase_init import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 ElektrAize API starting...")
    yield
    print("🛑 ElektrAize API shutting down...")

app = FastAPI(
    title="ElektrAize Energy Analytics",
    description="Firebase Auth + Energy Analytics Service",
    version="4.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domain'lerle değiştirin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="ElektrAize Energy Analytics",
        version="4.0",
        description="Firebase Auth + Energy Analytics Service",
        routes=app.routes,
    )
    
    components = openapi_schema.get("components", {})
    security_schemes = components.get("securitySchemes", {})
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    components["securitySchemes"] = security_schemes
    openapi_schema["components"] = components
    
    # Global security - tüm endpoint'ler için
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Routes
@app.get("/")
def root():
    return {
        "service": "ElektrAize Gateway",
        "docs": "/docs",
        "health": "/health",
        "me": "/me",
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ElektrAize Gateway"}

@app.get("/me")
def get_me(user=Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
    }

@app.get("/protected-test")
def protected_test(user=Depends(get_current_user)):
    return {"message": "This is a protected endpoint", "uid": user["uid"]}

@app.post("/send-verification")
def send_verification(id_token: str):
    """
    Send verification email to user via Firebase.
    id_token should be provided from frontend.
    """
    return send_verification_email(id_token)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)