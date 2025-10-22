import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, enum.Enum):
    CREATOR = "creator"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.CREATOR)
    locale: str = Field(default="ko")
    organization: Optional[str] = None
    name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_email_verified: bool = Field(default=False)
    password_login_enabled: bool = Field(default=True)
    privacy_consent: bool = Field(default=False)
    guidance_consent: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    password_set_at: Optional[datetime] = None

    channels: list["ChannelAccount"] = Relationship(back_populates="owner")
    managed_creators: list["ManagerCreatorLink"] = Relationship(back_populates="manager")
    managers: list["ManagerCreatorLink"] = Relationship(back_populates="creator")
    payments: list["Payment"] = Relationship(back_populates="user")
    social_accounts: list["SocialAccount"] = Relationship(back_populates="user")
    password_reset_tokens: list["PasswordResetToken"] = Relationship(back_populates="user")


class ChannelAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    platform: str
    account_name: str
    followers: int = 0
    growth_rate: float = 0.0
    engagement_rate: float = 0.0
    last_post_date: Optional[datetime] = None
    last_post_title: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, default=dict),
    )

    owner: User = Relationship(back_populates="channels")
    credential: Optional["ChannelCredential"] = Relationship(
        back_populates="channel",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )


class ManagerCreatorLink(SQLModel, table=True):
    manager_id: int = Field(foreign_key="user.id", primary_key=True)
    creator_id: int = Field(foreign_key="user.id", primary_key=True)
    approved: bool = Field(default=False)
    connected_at: datetime = Field(default_factory=datetime.utcnow)

    manager: User = Relationship(back_populates="managed_creators")
    creator: User = Relationship(back_populates="managers")


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    active: bool = Field(default=True)
    max_accounts: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    action: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[str] = None


class AuthType(str, enum.Enum):
    API_TOKEN = "api_token"
    USER_PASSWORD = "user_password"
    OAUTH2 = "oauth2"


class ChannelCredential(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel_id: int = Field(foreign_key="channelaccount.id", unique=True)
    auth_type: AuthType = Field(default=AuthType.API_TOKEN)
    identifier: Optional[str] = None
    secret_encrypted: Optional[str] = None
    access_token_encrypted: Optional[str] = None
    refresh_token_encrypted: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSON, nullable=False, default=dict),
    )

    channel: ChannelAccount = Relationship(back_populates="credential")

    @property
    def secret(self) -> Optional[str]:
        from .services.crypto import decrypt

        return decrypt(self.secret_encrypted)

    @secret.setter
    def secret(self, value: Optional[str]) -> None:
        from .services.crypto import encrypt

        self.secret_encrypted = encrypt(value)

    @property
    def access_token(self) -> Optional[str]:
        from .services.crypto import decrypt

        return decrypt(self.access_token_encrypted)

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        from .services.crypto import encrypt

        self.access_token_encrypted = encrypt(value)

    @property
    def refresh_token(self) -> Optional[str]:
        from .services.crypto import decrypt

        return decrypt(self.refresh_token_encrypted)

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        from .services.crypto import encrypt

        self.refresh_token_encrypted = encrypt(value)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "auth_type": self.auth_type.value,
            "identifier": self.identifier,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata_json,
            "has_secret": self.secret_encrypted is not None,
            "has_access_token": self.access_token_encrypted is not None,
            "has_refresh_token": self.refresh_token_encrypted is not None,
        }


class SocialProvider(str, enum.Enum):
    GOOGLE = "google"
    APPLE = "apple"
    EMAIL = "email"


class SocialAccount(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    provider: SocialProvider
    provider_user_id: str = Field(index=True)
    metadata_json: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, default=dict),
    )
    linked_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="social_accounts")


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: float = Field(default=0.0, ge=0)
    currency: str = Field(default="KRW")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    description: Optional[str] = None
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="payments")


class EmailVerification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    code_hash: str
    locale: str = Field(default="ko")
    verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    attempt_count: int = Field(default=0)


class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token_hash: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used: bool = Field(default=False)

    user: User = Relationship(back_populates="password_reset_tokens")
