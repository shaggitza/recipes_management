import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "recipes_db"
    app_title: str = "Recipe Management"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Logging configuration
    log_level: str = "INFO"
    use_structured_logging: bool = True
    
    # Environment detection
    environment: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()