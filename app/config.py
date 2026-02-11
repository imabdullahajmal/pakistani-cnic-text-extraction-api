import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CNIC Text Extraction API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    MODEL_PATH: str = "best.pt"
    UPLOAD_DIR: str = "uploads"

    # Detection
    DETECTION_THRESHOLD: float = 0.15

    # OCR
    OCR_LANG: str = "en"
    OCR_USE_ANGLE_CLS: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Upload limits
    MAX_FILE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists
UPLOAD_PATH = settings.BASE_DIR / settings.UPLOAD_DIR
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)

# Resolve model path
MODEL_PATH = settings.BASE_DIR / settings.MODEL_PATH
