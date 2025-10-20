from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import ActivityLog, ManagerCreatorLink, Subscription, User, UserRole
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
