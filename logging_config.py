# logging_config.py
"""
Merkezi logging konfigürasyonu - ElektrAize Backend
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Log dizini oluştur
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log dosyası adı (tarih bazında)
LOG_FILE = LOG_DIR / f"elektraize_{datetime.now().strftime('%Y%m%d')}.log"

# Log formatı
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level: str = "INFO", log_to_file: bool = True):
    """
    Merkezi logging konfigürasyonu
    
    Args:
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Dosyaya log yazılsın mı
    """
    # Root logger'ı yapılandır
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Mevcut handler'ları temizle (tekrar çağrıldığında duplicate önlemek için)
    root_logger.handlers.clear()
    
    # Formatter oluştur
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Console handler (her zaman)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (opsiyonel)
    if log_to_file:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Uvicorn ve FastAPI log seviyelerini ayarla
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Third-party log seviyelerini azalt
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Modül için logger al
    
    Args:
        name: Genellikle __name__ kullanılır
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Uygulama başlangıcında otomatik setup - sadece ana modülden çağrıldığında
# setup_logging() artık main.py'de manuel çağrılıyor, burada otomatik çağırmıyoruz
# Bu sayede import sırasında erken çalışmasını önlüyoruz

