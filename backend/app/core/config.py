from pydantic import BaseSettings, PostgresDsn
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MutualAid"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "mutualaid"
    DATABASE_URI: Optional[PostgresDsn] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Update database URI
if not settings.DATABASE_URI:
    settings.DATABASE_URI = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
