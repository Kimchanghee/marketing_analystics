from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "Creator Control Center"
    secret_key: str = Field("super-secret-key", env="APP_SECRET_KEY")
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    access_token_expire_minutes: int = 60 * 24

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
