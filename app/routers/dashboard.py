import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
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
from ..services.ai_recommendations import generate_ad_recommendations
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

    # AI 추천 생성
    ai_recommendations = {}
    for platform, snapshot in snapshots.items():
        recommendations = generate_ad_recommendations(snapshot)
        if recommendations:
            ai_recommendations[platform] = recommendations

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
            "ai_recommendations": ai_recommendations,
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
            credential.metadata_json = json.loads(metadata)
        except json.JSONDecodeError as exc:  # noqa: B904
            raise HTTPException(status_code=400, detail="Invalid metadata JSON") from exc

    session.add(credential)
    session.commit()
    session.refresh(credential)
    return {"message": "Credentials saved"}


@router.get("/dashboard/export/csv")
def export_dashboard_csv(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """대시보드 데이터를 CSV 형식으로 내보내기"""
    accounts = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == user.id)
        .options(selectinload(ChannelAccount.credential))
    ).all()
    snapshots = fetch_channel_snapshots(accounts)

    # CSV 생성
    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow([
        "플랫폼",
        "계정명",
        "구독자/팔로워",
        "성장률(%)",
        "참여율(%)",
        "최근 게시일",
        "최근 게시물 제목",
        "데이터 출처"
    ])

    # 데이터 행
    for account in accounts:
        snapshot = snapshots.get(account.platform, {})
        writer.writerow([
            account.platform,
            account.account_name,
            snapshot.get("followers", 0),
            snapshot.get("growth_rate", 0),
            snapshot.get("engagement_rate", 0),
            snapshot.get("last_post_date", "")[:10] if snapshot.get("last_post_date") else "-",
            snapshot.get("last_post_title", "-"),
            snapshot.get("source", "mock")
        ])

    # CSV 파일 반환
    output.seek(0)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_report_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/dashboard/export/json")
def export_dashboard_json(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """대시보드 데이터를 JSON 형식으로 내보내기"""
    accounts = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == user.id)
        .options(selectinload(ChannelAccount.credential))
    ).all()
    snapshots = fetch_channel_snapshots(accounts)

    # JSON 데이터 구성
    report_data = {
        "user": {
            "email": user.email,
            "name": user.name,
            "organization": user.organization,
        },
        "generated_at": datetime.utcnow().isoformat(),
        "channels": []
    }

    for account in accounts:
        snapshot = snapshots.get(account.id, {})
        channel_data = {
            "platform": account.platform,
            "account_name": account.account_name,
            "metrics": {
                "followers": snapshot.get("followers", 0),
                "growth_rate": snapshot.get("growth_rate", 0),
                "engagement_rate": snapshot.get("engagement_rate", 0),
            },
            "last_post": {
                "date": snapshot.get("last_post_date", ""),
                "title": snapshot.get("last_post_title", ""),
            },
            "recent_posts": snapshot.get("recent_posts", []),
            "hourly_views": snapshot.get("hourly_views", []),
            "data_source": snapshot.get("source", "mock")
        }
        report_data["channels"].append(channel_data)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_report_{timestamp}.json"

    return Response(
        content=json.dumps(report_data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/dashboard/export/pdf")
def export_dashboard_pdf(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """대시보드 데이터를 PDF 형식으로 내보내기"""
    from ..services.pdf_generator import generate_dashboard_pdf

    accounts = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == user.id)
        .options(selectinload(ChannelAccount.credential))
    ).all()
    snapshots = fetch_channel_snapshots(accounts)

    # PDF 생성
    pdf_buffer = generate_dashboard_pdf(user, accounts, snapshots)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_report_{timestamp}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
