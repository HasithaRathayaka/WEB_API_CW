from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "SLSEA Real-Time Solar Generation Data API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/slsea_solar_db",
        description="Database connection URL"
    )
    SECRET_KEY: str = Field(
        default="slsea_solar_super_secret_jwt_key_change_in_production_2026!",
        description="JWT cryptographic signing secret key"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
