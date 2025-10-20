from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_active_subscription, get_current_user
from ..models import ChannelAccount, ManagerCreatorLink, Subscription, SubscriptionTier, User, UserRole
from ..services.localization import translator
from ..services.social_fetcher import fetch_channel_snapshots

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(get_current_user), session=Depends(get_session)):
    locale = user.locale
    strings = translator.load_locale(locale)

    accounts = session.exec(select(ChannelAccount).where(ChannelAccount.owner_id == user.id)).all()
    account_payload = [
        {"platform": account.platform, "account_name": account.account_name}
        for account in accounts
    ]
    snapshots = fetch_channel_snapshots(account_payload)

    subscription = session.exec(select(Subscription).where(Subscription.user_id == user.id)).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE, max_accounts=1)
        session.add(subscription)
        session.commit()
        session.refresh(subscription)

    manager_links = []
    if user.role == UserRole.CREATOR:
        manager_links = session.exec(
            select(ManagerCreatorLink).where(ManagerCreatorLink.creator_id == user.id)
        ).all()
    elif user.role == UserRole.MANAGER:
        manager_links = session.exec(
            select(ManagerCreatorLink).where(ManagerCreatorLink.manager_id == user.id)
        ).all()

    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "user": user,
            "accounts": accounts,
            "snapshots": snapshots,
            "subscription": subscription,
            "manager_links": manager_links,
        },
    )


@router.post("/channels/add")
def add_channel(
    request: Request,
    platform: str = Form(...),
    account_name: str = Form(...),
    user: User = Depends(get_current_user),
    subscription: Subscription = Depends(get_active_subscription),
    session=Depends(get_session),
):
    current_accounts = session.exec(select(ChannelAccount).where(ChannelAccount.owner_id == user.id)).all()
    if len(current_accounts) >= subscription.max_accounts:
        raise HTTPException(status_code=402, detail="Subscription limit reached")

    channel = ChannelAccount(owner_id=user.id, platform=platform, account_name=account_name)
    session.add(channel)
    session.commit()
    return {"message": "Channel added"}


@router.post("/channels/remove")
def remove_channel(
    channel_id: int = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    channel = session.get(ChannelAccount, channel_id)
    if not channel or channel.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    session.delete(channel)
    session.commit()
    return {"message": "Channel removed"}
