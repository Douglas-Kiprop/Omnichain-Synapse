from pydantic import BaseSettings, validator
from typing import List
import os
import json


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    POSTGRES_URL: str = ""  # Supabase connection string
    
    # Authentication - Privy
    PRIVY_APP_ID: str = ""
    PRIVY_APP_SECRET: str = ""
    PRIVY_JWKS_URL: str = ""
    
    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "ES256"
    JWT_EXPIRE_HOURS: int = 24
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://your-frontend-domain.com"
    ]
    
    # External APIs
    COINGECKO_API_KEY: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    CHAINBASE_API_KEY: str = ""
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        # Accept list (already parsed), JSON string, or CSV
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            return [item.strip() for item in s.split(",") if item.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()