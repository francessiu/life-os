from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "LifeOS"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # Database (PostgreSQL)
    DATABASE_URL: str
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # OAuth Credentials
    GOOGLE_CLIENT_ID: str 
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/microsoft/callback"
    
    # Apple Credentials
    APPLE_CLIENT_ID: str    # Your "Services ID" (e.g., com.lifeos.web)
    APPLE_TEAM_ID: str      # Your Team ID (e.g., 8AB...)
    APPLE_KEY_ID: str       # The Key ID of your .p8 file
    APPLE_PRIVATE_KEY: str  # The content of your AuthKey_XXXX.p8 file

    # Paths
    PERSIST_DIRECTORY: str = "./backend/db/chroma_storage"
    
    class Config:
        env_file = ".env"

settings = Settings()