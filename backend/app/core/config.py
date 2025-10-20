from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_API_BASE: Optional[str] = None  # For custom LiteLLM or OpenAI-compatible endpoints
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_PROJECT_ID: Optional[str] = None  # For Pub/Sub (optional)
    
    # Hubspot OAuth
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    HUBSPOT_REDIRECT_URI: str
    
    # App Config
    SECRET_KEY: str
    FRONTEND_URL: str = "https://ai-advisor-frontend-59v2.onrender.com"
    BACKEND_URL: str = "https://ai-advisor-backend-02ky.onrender.com"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

