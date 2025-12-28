"""Input validation module."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_password_strength(password: str) -> str:
    """공통 비밀번호 강도 검증 함수.

    Args:
        password: 검증할 비밀번호

    Returns:
        검증된 비밀번호

    Raises:
        ValueError: 비밀번호가 요구사항을 충족하지 않는 경우
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")
    return password


class UserRegistration(BaseModel):
    """User registration input validation."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=50)
    role: str = Field(default="creator", pattern=r"^(creator|manager)$")
    organization: Optional[str] = Field(None, max_length=100)
    locale: str = Field(default="ko", pattern=r"^(ko|en|ja)$")
    privacy_agreement: bool
    guidance_agreement: bool

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        return _validate_password_strength(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate name."""
        if re.search(r'[!@#$%^&*()_+=\[\]{};:"\|,.<>/?]', v):
            raise ValueError("Name cannot contain special characters")
        return v.strip()


class UserLogin(BaseModel):
    """User login input validation."""

    email: EmailStr
    password: str
    locale: str = Field(default="ko", pattern=r"^(ko|en|ja)$")


class PasswordReset(BaseModel):
    """Password reset input validation."""

    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    locale: str = Field(default="ko", pattern=r"^(ko|en|ja)$")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        return _validate_password_strength(v)


class ChannelConnection(BaseModel):
    """Channel connection input validation."""

    platform: str = Field(
        ..., pattern=r"^(instagram|facebook|threads|youtube|twitter|tiktok)$"
    )
    account_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("account_name")
    @classmethod
    def validate_account_name(cls, v):
        """Validate account name."""
        if re.search(r'[\/:*?"<>|]', v):
            raise ValueError("Account name contains invalid characters")
        return v.strip()


class ChannelCredentials(BaseModel):
    """Channel credentials input validation."""

    auth_type: str = Field(..., pattern=r"^(oauth2|api_key|password)$")
    identifier: Optional[str] = Field(None, max_length=500)
    secret: Optional[str] = Field(None, max_length=500)
    access_token: Optional[str] = Field(None, max_length=2000)
    refresh_token: Optional[str] = Field(None, max_length=2000)
    expires_at: Optional[str] = None
    metadata: Optional[str] = None

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v):
        """Validate expiration time."""
        if v:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Invalid datetime format. Use ISO format.")
        return v

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v):
        """Validate metadata JSON."""
        if v:
            import json

            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for metadata")
        return v


class EmailVerification(BaseModel):
    """Email verification input validation."""

    email: EmailStr
    verification_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    locale: str = Field(default="ko", pattern=r"^(ko|en|ja)$")


class SocialLink(BaseModel):
    """Social account link input validation."""

    provider: str = Field(..., pattern=r"^(google|apple|facebook|twitter)$")
    provider_user_id: str = Field(..., min_length=1, max_length=200)


class SubscriptionChange(BaseModel):
    """Subscription change input validation."""

    tier: str = Field(..., pattern=r"^(free|pro|enterprise)$")


class ManagerLinkRequest(BaseModel):
    """Manager link request input validation."""

    manager_email: EmailStr


class ExportRequest(BaseModel):
    """Data export request input validation."""

    format: str = Field(..., pattern=r"^(csv|json|pdf)$")
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format."""
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        """Validate date range."""
        if v and info.data.get("start_date"):
            start = datetime.strptime(info.data["start_date"], "%Y-%m-%d")
            end = datetime.strptime(v, "%Y-%m-%d")
            if end < start:
                raise ValueError("End date must be after start date")
        return v


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input."""
    if not text:
        return ""

    text = text[:max_length]
    text = re.sub(r"<[^>]*>", "", text)
    text = text.replace("\0", "")
    text = text.replace("\x00", "")

    return text.strip()
