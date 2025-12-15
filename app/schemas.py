from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .models import SubscriptionTier, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.CREATOR
    locale: str = "ko"
    organization: Optional[str] = None
    name: Optional[str] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    locale: str
    organization: Optional[str]
    name: Optional[str]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChannelAccountCreate(BaseModel):
    platform: str
    account_name: str


class ChannelAccountRead(BaseModel):
    id: int
    platform: str
    account_name: str
    followers: int
    growth_rate: float
    engagement_rate: float
    last_post_date: Optional[datetime]
    last_post_title: Optional[str]

    class Config:
        orm_mode = True


class SubscriptionRead(BaseModel):
    tier: SubscriptionTier
    max_accounts: int
    active: bool


class ManagerApproval(BaseModel):
    manager_email: EmailStr
    approve: bool
