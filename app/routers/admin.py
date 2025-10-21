from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ..auth import auth_manager
from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import (
    ActivityLog,
    ManagerCreatorLink,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ..services.localization import translator

router = APIRouter()
REDIRECT_STATUS = status.HTTP_303_SEE_OTHER


@router.get("/super-admin")
def super_admin_dashboard(
    request: Request,
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    locale = user.locale
    strings = translator.load_locale(locale)
    status_key = request.query_params.get("status")
    status_type = request.query_params.get("type", "success")
    if status_type not in {"success", "error"}:
        status_type = "success"
    alerts = strings.get("super_admin", {}).get("alerts", {})
    status_message = alerts.get(status_key) if status_key else None
    users = session.exec(select(User)).all()
    subscriptions = session.exec(select(Subscription)).all()
    logs = session.exec(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(25)).all()
    return request.app.state.templates.TemplateResponse(
        "super_admin.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "users": users,
            "subscriptions": {subscription.user_id: subscription for subscription in subscriptions},
            "logs": logs,
            "status_message": status_message,
            "status_type": status_type,
        },
    )


@router.post("/super-admin/promote")
def promote_user(
    email: str = Form(...),
    role: UserRole = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.exec(select(User).where(User.email == email)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = role
    session.add(target)
    session.commit()
    return {"message": "Role updated"}


@router.post("/super-admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: UserRole = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.get(User, user_id)
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
    return RedirectResponse(
        url="/super-admin?status=role_updated&type=success",
        status_code=REDIRECT_STATUS,
    )


@router.post("/super-admin/users/{user_id}/profile")
def update_user_profile(
    user_id: int,
    locale: str = Form(...),
    organization: str = Form(""),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.locale = locale
    target.organization = organization or None
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="profile_update",
            details=f"{target.email}:{locale}",
        )
    )
    session.commit()
    return RedirectResponse(
        url="/super-admin?status=profile_updated&type=success",
        status_code=REDIRECT_STATUS,
    )


@router.post("/super-admin/users/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_active = is_active
    session.add(target)
    action = "reactivated" if is_active else "deactivated"
    session.add(
        ActivityLog(
            user_id=user.id,
            action=f"account_{action}",
            details=target.email,
        )
    )
    session.commit()
    status_key = "reactivated" if is_active else "deactivated"
    return RedirectResponse(
        url=f"/super-admin?status=status_{status_key}&type=success",
        status_code=REDIRECT_STATUS,
    )


@router.post("/super-admin/users/{user_id}/password")
def reset_user_password(
    user_id: int,
    password: str = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password too short")
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.hashed_password = auth_manager.hash_password(password)
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="password_reset",
            details=target.email,
        )
    )
    session.commit()
    return RedirectResponse(
        url="/super-admin?status=password_reset&type=success",
        status_code=REDIRECT_STATUS,
    )


@router.post("/super-admin/users/{user_id}/subscription")
def update_user_subscription(
    user_id: int,
    tier: SubscriptionTier = Form(...),
    max_accounts: int = Form(...),
    active: bool = Form(False),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    if max_accounts < 1:
        raise HTTPException(status_code=400, detail="Invalid account limit")
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == target.id)
    ).first()
    if not subscription:
        subscription = Subscription(user_id=target.id)
    subscription.tier = tier
    subscription.max_accounts = max_accounts
    subscription.active = active
    session.add(subscription)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="subscription_update",
            details=f"{target.email}:{tier.value}",
        )
    )
    session.commit()
    return RedirectResponse(
        url="/super-admin?status=subscription_updated&type=success",
        status_code=REDIRECT_STATUS,
    )


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
