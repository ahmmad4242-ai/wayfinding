"""
Configuration Management - إدارة الإعدادات
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """إعدادات التطبيق الرئيسية"""
    
    # Environment
    fpa_env: str = "production"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Database
    database_url: str = "postgresql://fpa_user:password@db:5432/fpa_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    cache_ttl: int = 3600
    
    # File Storage
    upload_dir: Path = Path("/app/data/uploads")
    output_dir: Path = Path("/app/data/outputs")
    cache_dir: Path = Path("/app/data/cache")
    max_upload_size: int = 52428800  # 50MB
    
    # Processing
    max_concurrent_jobs: int = 5
    job_timeout: int = 600
    
    # OCR Settings
    tesseract_lang: str = "ara+eng"
    ocr_dpi: int = 300
    enable_easyocr: bool = True
    
    # Detection Models
    yolo_model: str = "yolov8n.pt"
    yolo_confidence: float = 0.5
    yolo_iou: float = 0.45
    
    # Analysis Settings
    default_scale_unit: str = "meters"
    min_room_area: float = 2.0
    min_corridor_width: float = 1.2
    max_egress_distance: float = 60.0
    
    # Color Analysis
    color_palette_size: int = 10
    color_similarity_threshold: int = 30
    
    # Compliance
    default_building_code: str = "saudi_sbc"
    enable_ada_check: bool = True
    enable_fire_safety_check: bool = True
    
    # Security
    secret_key: str = "change-me-in-production"
    allowed_origins: List[str] = [
        "https://flows.aqeeli.com",
        "https://wfapi.aqeeli.com",
        "http://localhost:3000"
    ]
    
    # Monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    sentry_dsn: str = ""
    
    # External Services
    powerbi_api_key: str = ""
    ifc_export_enabled: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def ensure_directories():
    """إنشاء المجلدات المطلوبة"""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
