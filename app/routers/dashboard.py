import json
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import selectinload
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_active_subscription, get_current_user
from ..models import (
    AuthType,
    ChannelAccount,
    ChannelCredential,
    ManagerCreatorLink,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ..services.localization import translator
from ..services.social_fetcher import fetch_channel_snapshots

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(get_current_user), session=Depends(get_session)):
    locale = user.locale
    strings = translator.load_locale(locale)

    accounts = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == user.id)
        .options(selectinload(ChannelAccount.credential))
    ).all()
    snapshots = fetch_channel_snapshots(accounts)

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
            "auth_types": list(AuthType),
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


@router.post("/channels/credentials")
def upsert_channel_credentials(
    channel_id: int = Form(...),
    auth_type: str = Form(...),
    identifier: str | None = Form(None),
    secret: str | None = Form(None),
    access_token: str | None = Form(None),
    refresh_token: str | None = Form(None),
    expires_at: str | None = Form(None),
    metadata: str | None = Form(None),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    channel = session.get(ChannelAccount, channel_id)
    if not channel or channel.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    try:
        auth_enum = AuthType(auth_type)
    except ValueError as exc:  # noqa: B904
        raise HTTPException(status_code=400, detail="Invalid authentication type") from exc

    credential = channel.credential
    if credential is None:
        credential = ChannelCredential(channel_id=channel.id, auth_type=auth_enum)
        session.add(credential)

    credential.auth_type = auth_enum
    if identifier:
        credential.identifier = identifier
    if secret:
        credential.secret = secret
    if access_token:
        credential.access_token = access_token
    if refresh_token:
        credential.refresh_token = refresh_token
    if expires_at:
        try:
            credential.expires_at = datetime.fromisoformat(expires_at)
        except ValueError as exc:  # noqa: B904
            raise HTTPException(status_code=400, detail="Invalid expires_at format") from exc
    if metadata:
        try:
            credential.metadata = json.loads(metadata)
        except json.JSONDecodeError as exc:  # noqa: B904
            raise HTTPException(status_code=400, detail="Invalid metadata JSON") from exc

    session.add(credential)
    session.commit()
    session.refresh(credential)
    return {"message": "Credentials saved"}
