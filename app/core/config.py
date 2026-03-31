from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/webrtc_chat"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application
    APP_NAME: str = "WebRTC Chat"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"  # Игнорировать лишние поля


settings = Settings()