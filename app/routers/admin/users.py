"""
사용자 관리 라우터

사용자 역할, 상태, 구독 관리
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ...database import get_session
from ...dependencies import require_roles
from ...models import (
    ActivityLog,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)

router = APIRouter()


@router.post("/super-admin/promote")
def promote_user(
    request: Request,
    email: str = Form(...),
    role: UserRole = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """사용자 역할 변경"""
    target = session.exec(select(User).where(User.email == email)).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    target.role = role
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="role_update",
            details=f"{target.email}:{role.value}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/status")
def update_user_status(
    request: Request,
    user_id: int = Form(...),
    is_active: bool = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """사용자 활성화 상태 변경"""
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    target.is_active = is_active
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="user_status",
            details=f"{target.email}:{'active' if is_active else 'inactive'}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/subscription")
def update_subscription(
    request: Request,
    user_id: int = Form(...),
    tier: SubscriptionTier = Form(...),
    max_accounts: int = Form(1),
    active: bool = Form(False),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """사용자 구독 정보 변경"""
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == user_id)
    ).first()
    if not subscription:
        subscription = Subscription(user_id=user_id)
    subscription.tier = tier
    subscription.max_accounts = max(1, max_accounts)
    subscription.active = active
    session.add(subscription)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="subscription_update",
            details=f"{target.email}:{tier.value}:{'active' if active else 'inactive'}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)
