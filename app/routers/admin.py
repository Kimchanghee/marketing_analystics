from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import ActivityLog, ManagerCreatorLink, Subscription, SubscriptionTier, User, UserRole
from ..services.localization import translator

router = APIRouter()


@router.get("/super-admin")
def super_admin_dashboard(
    request: Request,
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    locale = user.locale
    strings = translator.load_locale(locale)
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
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
            "roles": list(UserRole),
            "tiers": list(SubscriptionTier),
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
    user_id: int = Form(...),
    is_active: bool = Form(...),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
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
    user_id: int = Form(...),
    tier: SubscriptionTier = Form(...),
    max_accounts: int = Form(1),
    active: bool = Form(False),
    user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
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
