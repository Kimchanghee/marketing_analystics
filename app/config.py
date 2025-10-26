from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "app.db"


class Settings(BaseSettings):
    app_name: str = "Creator Control Center"
    secret_key: str = Field("super-secret-key", env="SECRET_KEY")
    database_url: str = Field(f"sqlite:///{DEFAULT_DB_PATH}", env="DATABASE_URL")
    access_token_expire_minutes: int = 60 * 24
    verification_code_length: int = 6
    verification_code_expiry_minutes: int = 15
    password_reset_token_expiry_minutes: int = 30
    super_admin_access_token: str = Field("Ckdgml9788@", env="SUPER_ADMIN_ACCESS_TOKEN")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
