# error_handlers.py
"""
Merkezi error handling - ElektrAize Backend
Tutarlı JSON error response'ları ve güvenli hata yönetimi
"""
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from logging_config import get_logger

logger = get_logger(__name__)


# ===================== ERROR RESPONSE MODELLERİ =====================

class ErrorResponse:
    """Standart error response formatı"""
    
    @staticmethod
    def create(
        error_type: str,
        message: str,
        details: str = None,
        status_code: int = 500
    ) -> dict:
        """
        Standart error response oluştur
        
        Args:
            error_type: Hata tipi (örn: "ValidationError", "HTTPException")
            message: Kullanıcıya gösterilecek mesaj
            details: Ek detaylar (opsiyonel, production'da gizlenebilir)
            status_code: HTTP status code
        
        Returns:
            Standart error response dict
        """
        response = {
            "success": False,
            "error": {
                "type": error_type,
                "message": message
            }
        }
        
        # Details sadece development'ta veya güvenli hatalarda
        if details:
            response["error"]["details"] = details
        
        return response


# ===================== EXCEPTION HANDLERS =====================

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTPException handler - FastAPI'nin standart HTTP hataları
    """
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )
    
    error_response = ErrorResponse.create(
        error_type="HTTPException",
        message=exc.detail if exc.detail else "Bir hata oluştu",
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Pydantic ValidationError handler - Request validation hataları
    """
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {message}")
    
    error_detail = "; ".join(error_messages)
    
    logger.warning(
        f"ValidationError: {error_detail} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )
    
    error_response = ErrorResponse.create(
        error_type="ValidationError",
        message="İstek doğrulama hatası",
        details=error_detail,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Generic Exception handler - Beklenmeyen hatalar
    ÖNEMLİ: Stack trace'i client'a gönderme, sadece server-side logla
    """
    # Full stack trace'i server-side logla
    logger.exception(
        f"Unexpected error: {type(exc).__name__} - {str(exc)} | "
        f"Path: {request.url.path} | Method: {request.method}"
    )
    
    # Client'a güvenli, generic mesaj gönder
    error_response = ErrorResponse.create(
        error_type="InternalServerError",
        message="Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    # Development modunda detay göster (opsiyonel)
    import os
    if os.getenv("ENVIRONMENT", "production").lower() == "development":
        error_response["error"]["details"] = f"{type(exc).__name__}: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# ===================== CUSTOM EXCEPTIONS =====================

class ElektrAizeException(HTTPException):
    """Base exception for ElektrAize-specific errors"""
    def __init__(self, message: str, status_code: int = 500, details: str = None):
        super().__init__(status_code=status_code, detail=message)
        self.details = details


class ModelNotLoadedException(ElektrAizeException):
    """Model yüklenmediğinde fırlatılır"""
    def __init__(self, category: str):
        super().__init__(
            message=f"'{category}' kategorisi için model yüklenmemiş",
            status_code=503,
            details=f"Model yüklenemedi: {category}"
        )


class DataNotFoundException(ElektrAizeException):
    """Veri bulunamadığında fırlatılır"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} bulunamadı"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            status_code=404,
            details=f"Resource: {resource}, Identifier: {identifier}"
        )

