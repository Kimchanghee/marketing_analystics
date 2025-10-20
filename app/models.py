import enum
from datetime import datetime
from typing import Optional

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

    channels: list["ChannelAccount"] = Relationship(back_populates="owner")
    managed_creators: list["ManagerCreatorLink"] = Relationship(back_populates="manager")
    managers: list["ManagerCreatorLink"] = Relationship(back_populates="creator")


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
    extra_metadata: dict = Field(default_factory=dict, sa_column_kwargs={"nullable": False})

    owner: User = Relationship(back_populates="channels")


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
