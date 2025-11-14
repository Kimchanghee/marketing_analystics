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
    apple_client_id: str = Field("", env="APPLE_CLIENT_ID")
    apple_team_id: str = Field("", env="APPLE_TEAM_ID")
    apple_key_id: str = Field("", env="APPLE_KEY_ID")
    apple_private_key: str = Field("", env="APPLE_PRIVATE_KEY")
    super_admin_email: str = Field("", env="SUPER_ADMIN_EMAIL")
    super_admin_email_password: str = Field("", env="SUPER_ADMIN_EMAIL_PASSWORD")
    smtp_host: str = Field("smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")
    imap_host: str = Field("imap.gmail.com", env="IMAP_HOST")
    imap_port: int = Field(993, env="IMAP_PORT")
    imap_use_ssl: bool = Field(True, env="IMAP_USE_SSL")
    imap_sent_folder: str = Field("[Gmail]/Sent Mail", env="IMAP_SENT_FOLDER")

    # Gmail API 설정 (SMTP/IMAP 대체)
    gmail_sender_email: str = Field("", env="GMAIL_SENDER_EMAIL")
    google_service_account_file: str = Field("", env="GOOGLE_SERVICE_ACCOUNT_FILE")
    gmail_delegated_email: str = Field("", env="GMAIL_DELEGATED_EMAIL")  # Domain-wide delegation
    gmail_credentials_json: str = Field("", env="GMAIL_CREDENTIALS_JSON")  # OAuth2 credentials

    @property
    def is_production(self) -> bool:
        """Check if running in production environment (Cloud Run)"""
        return self.environment.lower() == "production"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
