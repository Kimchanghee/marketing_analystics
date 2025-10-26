from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import select

from .auth import auth_manager
from .database import get_session
from .models import Subscription, SubscriptionTier, User, UserRole


def get_current_user(request: Request, session=Depends(get_session)) -> User:
    token: Optional[str] = auth_manager.extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    email = auth_manager.decode_token(token)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    return user


def require_roles(*roles: UserRole):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        # SUPER_ADMIN은 모든 페이지에 접근 가능
        if user.role == UserRole.SUPER_ADMIN:
            return user
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return role_checker


def get_active_subscription(user: User = Depends(get_current_user), session=Depends(get_session)) -> Subscription:
    subscription = session.exec(select(Subscription).where(Subscription.user_id == user.id)).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE, max_accounts=1)
        session.add(subscription)
        session.commit()
        session.refresh(subscription)
    return subscription
