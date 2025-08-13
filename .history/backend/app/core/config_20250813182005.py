from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://kbeye:kbeye_password@localhost:5432/kbeye"
    
    # App settings
    APP_NAME: str = "KbEye"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Config file paths
    CONFIG_PATH: str = "/app/config"
    SERVICES_CONFIG_FILE: str = "services.json"
    ALERTS_CONFIG_FILE: str = "alerts.json"
    SETTINGS_CONFIG_FILE: str = "settings.json"
    
    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()