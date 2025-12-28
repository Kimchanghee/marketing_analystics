from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "app.db"


class Settings(BaseSettings):
    app_name: str = "Creator Control Center"
    # SECURITY: No default values for secrets! Must be set in .env file
    secret_key: str = Field(..., env="SECRET_KEY")
    database_url: str = Field(f"sqlite:///{DEFAULT_DB_PATH}", env="DATABASE_URL")
    access_token_expire_minutes: int = 60 * 24
    verification_code_length: int = 6
    verification_code_expiry_minutes: int = 15
    password_reset_token_expiry_minutes: int = 30
    # SECURITY: No default values for admin tokens! Must be set in .env file
    super_admin_access_token: str = Field(..., env="SUPER_ADMIN_ACCESS_TOKEN")
    gemini_api_key: str = Field("", env="GEMINI_API_KEY")
    environment: str = Field("development", env="ENVIRONMENT")  # production or development

    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        """환경 변수 검증"""
        # 환경 값 검증
        valid_environments = ["development", "production", "staging", "test"]
        if self.environment.lower() not in valid_environments:
            raise ValueError(
                f"Invalid ENVIRONMENT: '{self.environment}'. "
                f"Must be one of: {', '.join(valid_environments)}"
            )

        # 프로덕션 환경에서 필수 설정 검증
        if self.is_production:
            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError(
                    "Production requires SECRET_KEY with at least 32 characters"
                )
            if not self.super_admin_access_token or len(self.super_admin_access_token) < 16:
                raise ValueError(
                    "Production requires SUPER_ADMIN_ACCESS_TOKEN with at least 16 characters"
                )
            if "sqlite" in self.database_url.lower():
                import warnings
                warnings.warn(
                    "Using SQLite in production is not recommended. "
                    "Consider using PostgreSQL.",
                    UserWarning
                )

        return self

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

    # Supabase 설정 (DATABASE_URL에 Supabase PostgreSQL URL 사용)
    supabase_url: str = Field("", env="SUPABASE_URL")
    supabase_anon_key: str = Field("", env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field("", env="SUPABASE_SERVICE_ROLE_KEY")

    # Resend 이메일 서비스 설정
    resend_api_key: str = Field("", env="RESEND_API_KEY")
    resend_from_email: str = Field("noreply@yourdomain.com", env="RESEND_FROM_EMAIL")
    resend_from_name: str = Field("Creator Control Center", env="RESEND_FROM_NAME")

    @property
    def use_resend(self) -> bool:
        """Resend API 사용 여부"""
        return bool(self.resend_api_key)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment (Cloud Run)"""
        return self.environment.lower() == "production"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
