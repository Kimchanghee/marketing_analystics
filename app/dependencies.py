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


def require_subscription_tier(*required_tiers: SubscriptionTier):
    """
    특정 구독 티어 이상의 사용자만 접근 가능하도록 제한합니다.

    사용 예:
    - require_subscription_tier(SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE)
    - require_subscription_tier(SubscriptionTier.ENTERPRISE)
    """
    def subscription_checker(
        user: User = Depends(get_current_user),
        subscription: Subscription = Depends(get_active_subscription)
    ) -> Subscription:
        # SUPER_ADMIN은 모든 기능 접근 가능
        if user.role == UserRole.SUPER_ADMIN:
            return subscription

        # 구독이 활성화되어 있지 않으면 거부
        if not subscription.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription is not active. Please activate your subscription."
            )

        # 요구되는 티어 중 하나에 해당하는지 확인
        if subscription.tier not in required_tiers:
            tier_names = ", ".join([tier.value.upper() for tier in required_tiers])
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires {tier_names} subscription. Please upgrade your plan."
            )

        return subscription

    return subscription_checker


def check_feature_access(feature: str):
    """
    특정 기능에 대한 접근 권한을 확인합니다.

    기능별 필요 티어:
    - ai_recommendations: PRO 이상
    - ai_pd: PRO 이상
    - advanced_analytics: PRO 이상
    - api_access: ENTERPRISE
    - unlimited_channels: ENTERPRISE
    - team_collaboration: ENTERPRISE
    """
    FEATURE_TIER_MAP = {
        "ai_recommendations": [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE],
        "ai_pd": [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE],
        "advanced_analytics": [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE],
        "export_data": [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE],
        "api_access": [SubscriptionTier.ENTERPRISE],
        "unlimited_channels": [SubscriptionTier.ENTERPRISE],
        "team_collaboration": [SubscriptionTier.ENTERPRISE],
        "priority_support": [SubscriptionTier.ENTERPRISE],
    }

    def feature_checker(
        user: User = Depends(get_current_user),
        subscription: Subscription = Depends(get_active_subscription)
    ) -> bool:
        # SUPER_ADMIN은 모든 기능 접근 가능
        if user.role == UserRole.SUPER_ADMIN:
            return True

        # 구독이 활성화되어 있지 않으면 무료 기능만 가능
        if not subscription.active:
            return False

        # 기능에 필요한 티어 확인
        required_tiers = FEATURE_TIER_MAP.get(feature, [SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE])

        if subscription.tier not in required_tiers:
            tier_names = ", ".join([tier.value.upper() for tier in required_tiers])
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires {tier_names} subscription. Please upgrade your plan."
            )

        return True

    return feature_checker
