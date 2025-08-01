import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://mongodb:27017"
    database_name: str = "recipes_db"
    app_title: str = "Recipe Management"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()