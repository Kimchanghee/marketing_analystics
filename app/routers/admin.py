from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ..config import get_settings
from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import (
    ActivityLog,
    ManagerCreatorLink,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ..services.localization import translator

router = APIRouter()


def verify_admin_token(request: Request):
    """관리자 페이지 접속 토큰 확인"""
    settings = get_settings()
    # 쿼리 파라미터에서 토큰 확인
    token = request.query_params.get("admin_token")
    # 쿠키에서 토큰 확인
    cookie_token = request.cookies.get("admin_access_token")

    if token == settings.super_admin_access_token:
        return token
    elif cookie_token == settings.super_admin_access_token:
        return cookie_token
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 페이지 접속 토큰이 필요합니다. URL에 ?admin_token=YOUR_TOKEN을 추가하세요."
        )


@router.get("/super-admin")
def super_admin_dashboard(
    request: Request,
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
    admin_token: str = Depends(verify_admin_token),
):
    locale = user.locale
    strings = translator.load_locale(locale)
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    subscriptions = session.exec(select(Subscription)).all()
    payments = session.exec(select(Payment).order_by(Payment.created_at.desc()).limit(50)).all()
    user_lookup = {u.id: u for u in users}
    logs = session.exec(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(25)).all()

    response = request.app.state.templates.TemplateResponse(
        "super_admin.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "users": users,
            "subscriptions": {subscription.user_id: subscription for subscription in subscriptions},
            "logs": logs,
            "roles": list(UserRole),
            "tiers": list(SubscriptionTier),
            "payment_statuses": list(PaymentStatus),
            "payments": payments,
            "user_lookup": user_lookup,
        },
    )

    # 쿼리 파라미터로 토큰이 전달된 경우 쿠키에 저장
    if request.query_params.get("admin_token"):
        response.set_cookie(
            key="admin_access_token",
            value=admin_token,
            httponly=True,
            max_age=60 * 60 * 24  # 24시간 유효
        )

    return response


@router.post("/super-admin/promote")
def promote_user(
    request: Request,
    email: str = Form(...),
    role: UserRole = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
    admin_token: str = Depends(verify_admin_token),
):
    target = session.exec(select(User).where(User.email == email)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
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
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
    admin_token: str = Depends(verify_admin_token),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
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
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
    admin_token: str = Depends(verify_admin_token),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    subscription = session.exec(select(Subscription).where(Subscription.user_id == user_id)).first()
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


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@router.post("/super-admin/payment/create")
def create_payment(
    request: Request,
    user_id: int = Form(...),
    amount: float = Form(...),
    currency: str = Form("KRW"),
    status_value: PaymentStatus = Form(PaymentStatus.PENDING),
    description: str | None = Form(None),
    billing_period_start: str | None = Form(None),
    billing_period_end: str | None = Form(None),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
    admin_token: str = Depends(verify_admin_token),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    currency_value = (currency or "KRW").strip().upper()[:3] or "KRW"
    payment = Payment(
        user_id=user_id,
        amount=max(amount, 0),
        currency=currency_value,
        status=status_value,
        description=description.strip() if description else None,
        billing_period_start=_parse_datetime(billing_period_start),
        billing_period_end=_parse_datetime(billing_period_end),
    )
    session.add(payment)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="payment_create",
            details=f"{target.email}:{payment.amount}{payment.currency}:{payment.status.value}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/payment/status")
def update_payment_status(
    request: Request,
    payment_id: int = Form(...),
    status_value: PaymentStatus = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
    admin_token: str = Depends(verify_admin_token),
):
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = status_value
    session.add(payment)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="payment_status",
            details=f"{payment.id}:{payment.status.value}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/manager/approve")
def approve_manager(
    creator_email: str = Form(...),
    manager_email: str = Form(...),
    approve: bool = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    creator = session.exec(select(User).where(User.email == creator_email)).first()
    manager = session.exec(select(User).where(User.email == manager_email)).first()
    if not creator or not manager:
        raise HTTPException(status_code=404, detail="User not found")

    link = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.creator_id == creator.id)
        .where(ManagerCreatorLink.manager_id == manager.id)
    ).first()

    if not link:
        link = ManagerCreatorLink(creator_id=creator.id, manager_id=manager.id, approved=approve)
    else:
        link.approved = approve

    session.add(link)
    session.commit()
    return {"message": "Approval updated"}
