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

    channels: list["ChannelAccount"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}  # User 삭제 시 채널도 삭제
    )
    managed_creators: list["ManagerCreatorLink"] = Relationship(
        back_populates="manager",
        sa_relationship_kwargs={
            "foreign_keys": "ManagerCreatorLink.manager_id",
            "cascade": "all, delete-orphan"  # User 삭제 시 매니저 링크도 삭제
        }
    )
    managers: list["ManagerCreatorLink"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={
            "foreign_keys": "ManagerCreatorLink.creator_id",
            "cascade": "all, delete-orphan"  # User 삭제 시 크리에이터 링크도 삭제
        }
    )
    payments: list["Payment"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}  # User 삭제 시 결제 내역도 삭제 (GDPR 준수)
    )
    social_accounts: list["SocialAccount"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}  # User 삭제 시 소셜 계정도 삭제
    )
    password_reset_tokens: list["PasswordResetToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}  # User 삭제 시 토큰도 삭제
    )


class ChannelAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)  # 인덱스 추가 (조회 성능 향상)
    platform: str
    account_name: str
    followers: int = 0
    growth_rate: float = 0.0
    engagement_rate: float = 0.0
    last_post_date: Optional[datetime] = None
    last_post_title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # 정렬용 인덱스
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
    approved: bool = Field(default=False, index=True)  # 필터링 성능 향상
    connected_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # 정렬용 인덱스

    manager: User = Relationship(
        back_populates="managed_creators",
        sa_relationship_kwargs={"foreign_keys": "[ManagerCreatorLink.manager_id]"}
    )
    creator: User = Relationship(
        back_populates="managers",
        sa_relationship_kwargs={"foreign_keys": "[ManagerCreatorLink.creator_id]"}
    )


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)  # 조회 성능 향상
    tier: SubscriptionTier = Field(default=SubscriptionTier.FREE, index=True)  # 필터링 성능 향상
    active: bool = Field(default=True, index=True)  # 활성 구독 필터링
    max_accounts: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # 정렬용 인덱스


class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)  # 사용자별 로그 조회 성능 향상
    action: str = Field(index=True)  # 액션별 필터링 성능 향상
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # 정렬용 인덱스
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
    user_id: int = Field(foreign_key="user.id", index=True)  # 사용자별 결제 조회 성능 향상
    amount: float = Field(default=0.0, ge=0)
    currency: str = Field(default="KRW")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)  # 상태별 필터링 성능 향상
    description: Optional[str] = None
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # 정렬용 인덱스

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


class ManagerAPIKey(SQLModel, table=True):
    """기업 관리자의 암호화된 Gemini API 키 저장"""
    id: Optional[int] = Field(default=None, primary_key=True)
    manager_id: int = Field(foreign_key="user.id", unique=True)
    api_key_encrypted: str
    service_name: str = Field(default="gemini")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def api_key(self) -> str:
        """Decrypt and return the API key.

        Returns:
            Decrypted API key

        Raises:
            DecryptionError: If decryption fails (corrupted data or wrong key)
        """
        from .services.crypto import decrypt, DecryptionError

        decrypted = decrypt(self.api_key_encrypted)
        if decrypted is None:
            # This should not happen since api_key_encrypted is required, but handle it safely
            raise ValueError("API key is missing or empty")
        return decrypted

    @api_key.setter
    def api_key(self, value: str) -> None:
        from .services.crypto import encrypt
        self.api_key_encrypted = encrypt(value)
        self.updated_at = datetime.utcnow()


class InquiryStatus(str, enum.Enum):
    """문의 상태"""
    PENDING = "pending"  # 대기 중
    IN_PROGRESS = "in_progress"  # 처리 중
    AI_DRAFT_READY = "ai_draft_ready"  # AI 답변 초안 준비됨
    ANSWERED = "answered"  # 답변 완료
    CLOSED = "closed"  # 종결


class InquiryCategory(str, enum.Enum):
    """문의 카테고리"""
    TECHNICAL = "technical"  # 기술 문의
    ACCOUNT = "account"  # 계정 문의
    BILLING = "billing"  # 결제 문의
    FEATURE_REQUEST = "feature_request"  # 기능 요청
    BUG_REPORT = "bug_report"  # 버그 신고
    GENERAL = "general"  # 일반 문의


class CreatorInquiry(SQLModel, table=True):
    """크리에이터 문의/이슈 관리"""
    id: Optional[int] = Field(default=None, primary_key=True)
    creator_id: int = Field(foreign_key="user.id", index=True)  # 크리에이터별 문의 조회 성능 향상
    manager_id: int = Field(foreign_key="user.id", index=True)  # 매니저별 문의 조회 성능 향상
    category: InquiryCategory = Field(default=InquiryCategory.GENERAL, index=True)  # 카테고리별 필터링
    subject: str
    message: str
    status: InquiryStatus = Field(default=InquiryStatus.PENDING, index=True)  # 상태별 필터링 성능 향상
    ai_draft_response: Optional[str] = None
    final_response: Optional[str] = None
    context_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("context_data", JSON, nullable=False, default=dict),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # 정렬용 인덱스
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
