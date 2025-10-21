from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import select

from ..auth import auth_manager
from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import (
    ActivityLog,
    ChannelAccount,
    ManagerCreatorLink,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ..services.localization import translator

from sqlalchemy import or_

router = APIRouter()


@router.get("/super-admin")
def super_admin_dashboard(
    request: Request,
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    locale = user.locale
    strings = translator.load_locale(locale)
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


@router.post("/super-admin/users")
def create_user(
    email: EmailStr = Form(...),
    password: str = Form(...),
    role: UserRole = Form(UserRole.CREATOR),
    locale: str = Form("ko"),
    organization: str | None = Form(None),
    subscription_tier: SubscriptionTier = Form(SubscriptionTier.FREE),
    max_accounts: int = Form(1),
    active: bool = Form(False),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        return RedirectResponse(
            url="/super-admin?error=user_exists", status_code=status.HTTP_303_SEE_OTHER
        )

    if len(password) < 8:
        return RedirectResponse(
            url="/super-admin?error=password_short", status_code=status.HTTP_303_SEE_OTHER
        )

    safe_max_accounts = max(1, max_accounts)
    hashed_password = auth_manager.hash_password(password)
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        locale=locale,
        organization=organization or None,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    subscription = Subscription(
        user_id=new_user.id,
        tier=subscription_tier,
        active=active,
        max_accounts=safe_max_accounts,
    )
    session.add(subscription)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="admin_create_user",
            details=f"created {new_user.email}",
        )
    )
    session.commit()

    redirect_url = "/super-admin?flash=user_created"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/users/{user_id}/update")
def update_user(
    user_id: int,
    role: UserRole = Form(...),
    locale: str = Form(...),
    organization: str | None = Form(None),
    subscription_tier: SubscriptionTier = Form(...),
    max_accounts: int = Form(1),
    active: bool = Form(False),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        return RedirectResponse(
            url="/super-admin?error=user_missing", status_code=status.HTTP_303_SEE_OTHER
        )

    target.role = role
    target.locale = locale
    target.organization = organization or None

    subscription = session.exec(select(Subscription).where(Subscription.user_id == target.id)).first()
    if not subscription:
        subscription = Subscription(user_id=target.id)

    subscription.tier = subscription_tier
    subscription.max_accounts = max(1, max_accounts)
    subscription.active = active

    session.add(target)
    session.add(subscription)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="admin_update_user",
            details=f"updated {target.email}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?flash=user_updated", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/super-admin/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    new_password: str = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        return RedirectResponse(
            url="/super-admin?error=user_missing", status_code=status.HTTP_303_SEE_OTHER
        )

    if len(new_password) < 8:
        return RedirectResponse(
            url="/super-admin?error=password_short", status_code=status.HTTP_303_SEE_OTHER
        )

    target.hashed_password = auth_manager.hash_password(new_password)
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="admin_reset_password",
            details=f"reset password for {target.email}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?flash=password_reset", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/super-admin/users/{user_id}/delete")
def delete_user(
    user_id: int,
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    target = session.get(User, user_id)
    if not target:
        return RedirectResponse(
            url="/super-admin?error=user_missing", status_code=status.HTTP_303_SEE_OTHER
        )

    if target.id == user.id:
        return RedirectResponse(
            url="/super-admin?error=cannot_delete_self",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    channel_accounts = session.exec(
        select(ChannelAccount).where(ChannelAccount.owner_id == target.id)
    ).all()
    for account in channel_accounts:
        session.delete(account)

    links = session.exec(
        select(ManagerCreatorLink).where(
            or_(
                ManagerCreatorLink.creator_id == target.id,
                ManagerCreatorLink.manager_id == target.id,
            )
        )
    ).all()
    for link in links:
        session.delete(link)

    subscription = session.exec(select(Subscription).where(Subscription.user_id == target.id)).all()
    for sub in subscription:
        session.delete(sub)

    activity_logs = session.exec(select(ActivityLog).where(ActivityLog.user_id == target.id)).all()
    for log in activity_logs:
        session.delete(log)

    session.delete(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="admin_delete_user",
            details=f"deleted {target.email}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?flash=user_deleted", status_code=status.HTTP_303_SEE_OTHER
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
