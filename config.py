"""
Configuration settings for BDD Test Generator
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    """Application configuration"""
    
    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).parent
    OUTPUT_DIR: Path = PROJECT_ROOT / "output" / "features"
    CACHE_DIR: Path = PROJECT_ROOT / ".cache"
    CACHE_DB_PATH: Path = CACHE_DIR / "dom_cache.db"
    
    # Browser Settings
    HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 900000000  # milliseconds
    VIEWPORT_WIDTH: int = 1920
    VIEWPORT_HEIGHT: int = 1080
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Ollama Settings
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"  # or "mistral", "llama2"
    OLLAMA_TIMEOUT: int = 120
    
    # Detection Settings
    MAX_HOVER_ELEMENTS: int = 25    
    MAX_POPUP_TRIGGERS: int = 10
    HOVER_WAIT_TIME: float = 5  # seconds
    INTERACTION_TIMEOUT: int = 25  # seconds
    
    # Cache Settings
    USE_CACHE: bool = True
    CACHE_EXPIRY_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


    # QUALITY_MIN_STEPS = 3
    # QUALITY_MAX_GENERIC_PHRASES = 2
    # QUALITY_MIN_CONFIDENCE = 0.6

    # ENABLE_DEDUPLICATION = True
    # ENABLE_QUALITY_CHECK = True
    # ENABLE_IMPROVEMENTS = True
    
    # AI Agent Settings
    MAX_RETRIES: int = 3
    TEMPERATURE: float = 0.7
    
    # API Settings (FastAPI)
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global config instance
config = Config()

# Create necessary directories
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
config.CACHE_DIR.mkdir(parents=True, exist_ok=True)