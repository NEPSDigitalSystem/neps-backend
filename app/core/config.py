
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


def get_secret_from_file(secret_path: Optional[str]) -> Optional[str]:
    """Read a secret from a file (Docker secrets support)."""
    if not secret_path:
        return None
    try:
        with open(secret_path, "r") as f:
            return f.read().strip()
    except Exception:
        return None


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "NEPS Digital Backend"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "neps_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Secret files (Docker)
    DATABASE_USER_FILE: Optional[str] = None
    DATABASE_PASSWORD_FILE: Optional[str] = None

    # REDCap
    REDCAP_API_URL: str = "http://localhost:8000/api/redcap"
    REDCAP_API_TOKEN: Optional[str] = None
    REDCAP_PROJECT_ID: str = "NEPS-2025"
    REDCAP_MOCK_ENABLED: bool = True
    REDCAP_API_TOKEN_FILE: Optional[str] = None

    # JWT & Security
    SECRET_KEY: Optional[str] = None
    SECRET_KEY_FILE: Optional[str] = None
    JWT_ALGORITHM: str = "ES256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 50

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_user(self) -> str:
        if self.DATABASE_USER_FILE:
            secret = get_secret_from_file(self.DATABASE_USER_FILE)
            if secret:
                return secret
        return self.DATABASE_USER or "neps"

    @property
    def database_password(self) -> str:
        if self.DATABASE_PASSWORD_FILE:
            secret = get_secret_from_file(self.DATABASE_PASSWORD_FILE)
            if secret:
                return secret
        return self.DATABASE_PASSWORD or "neps_password"

    @property
    def redcap_api_token(self) -> Optional[str]:
        if self.REDCAP_API_TOKEN_FILE:
            secret = get_secret_from_file(self.REDCAP_API_TOKEN_FILE)
            if secret:
                return secret
        return self.REDCAP_API_TOKEN

    @property
    def secret_key(self) -> Optional[str]:
        if self.SECRET_KEY_FILE:
            secret = get_secret_from_file(self.SECRET_KEY_FILE)
            if secret:
                return secret
        return self.SECRET_KEY

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.database_user}:{self.database_password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.database_user}:{self.database_password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
