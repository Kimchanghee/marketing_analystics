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
    gemini_api_key: str = Field("", env="GEMINI_API_KEY")
    environment: str = Field("production", env="ENVIRONMENT")  # production or development

    # OAuth 2.0 설정
    facebook_app_id: str = Field("", env="FACEBOOK_APP_ID")
    facebook_app_secret: str = Field("", env="FACEBOOK_APP_SECRET")
    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", env="GOOGLE_CLIENT_SECRET")
    twitter_client_id: str = Field("", env="TWITTER_CLIENT_ID")
    twitter_client_secret: str = Field("", env="TWITTER_CLIENT_SECRET")
    tiktok_client_key: str = Field("", env="TIKTOK_CLIENT_KEY")
    tiktok_client_secret: str = Field("", env="TIKTOK_CLIENT_SECRET")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment (Cloud Run)"""
        return self.environment.lower() == "production"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
