"""AI PD (Personal Development) Router

Provides AI-powered analysis and feedback for creators and managers.
This is a premium feature that requires valid API keys.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import selectinload
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_current_user
from ..models import (
    ChannelAccount,
    ManagerCreatorLink,
    User,
    UserRole,
)
from ..services.ai_pd_service import ai_pd_service
from ..services.localization import translator
from ..services.social_fetcher import fetch_channel_snapshots

router = APIRouter()


@router.get("/ai-pd")
def ai_pd_dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """AI PD dashboard - available for both creators and managers"""
    locale = user.locale
    strings = translator.load_locale(locale)

    # Determine user type and fetch relevant data
    if user.role == UserRole.CREATOR:
        # Get creator's channels
        channels = session.exec(
            select(ChannelAccount)
            .where(ChannelAccount.owner_id == user.id)
            .options(selectinload(ChannelAccount.credential))
        ).all()
        snapshots = fetch_channel_snapshots(channels)

        template_data = {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "user_type": "creator",
            "channels": channels,
            "snapshots": snapshots,
            "total_followers": sum(s.get('followers', 0) for s in snapshots.values()),
            "avg_engagement": sum(s.get('engagement_rate', 0) for s in snapshots.values()) / len(snapshots) if snapshots else 0,
        }

    elif user.role in [UserRole.MANAGER, UserRole.ADMIN]:
        # Get managed creators
        links = session.exec(
            select(ManagerCreatorLink)
            .where(ManagerCreatorLink.manager_id == user.id)
            .where(ManagerCreatorLink.approved == True)
        ).all()

        creator_ids = [link.creator_id for link in links]
        creators = session.exec(
            select(User).where(User.id.in_(creator_ids))
        ).all() if creator_ids else []

        # Get all channels for all creators
        all_channels: Dict[int, List[ChannelAccount]] = {}
        all_snapshots: Dict[int, Dict[int, Dict]] = {}
        total_channels = 0
        total_followers = 0

        for creator in creators:
            channels = session.exec(
                select(ChannelAccount)
                .where(ChannelAccount.owner_id == creator.id)
                .options(selectinload(ChannelAccount.credential))
            ).all()
            all_channels[creator.id] = list(channels)
            snapshots = fetch_channel_snapshots(channels)
            all_snapshots[creator.id] = snapshots

            total_channels += len(channels)
            total_followers += sum(s.get('followers', 0) for s in snapshots.values())

        template_data = {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "user_type": "manager",
            "creators": creators,
            "all_channels": all_channels,
            "all_snapshots": all_snapshots,
            "total_creators": len(creators),
            "total_channels": total_channels,
            "total_followers": total_followers,
        }

    else:
        raise HTTPException(status_code=403, detail="AI PD 서비스는 크리에이터와 매니저만 이용할 수 있습니다.")

    return request.app.state.templates.TemplateResponse(
        "ai_pd_dashboard.html",
        template_data
    )


@router.post("/ai-pd/ask")
def ask_ai_pd(
    request: Request,
    question: str = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session)
):
    """Ask AI PD a question about performance and get insights"""
    if not question or len(question.strip()) < 10:
        raise HTTPException(status_code=400, detail="질문은 최소 10자 이상 입력해주세요.")

    try:
        if user.role == UserRole.CREATOR:
            # Creator asking about their own channels
            channels = session.exec(
                select(ChannelAccount)
                .where(ChannelAccount.owner_id == user.id)
                .options(selectinload(ChannelAccount.credential))
            ).all()
            snapshots = fetch_channel_snapshots(channels)

            # Convert snapshots from {id: data} to {id: data} format expected
            snapshot_dict = {ch.id: snapshots.get(ch.id, {}) for ch in channels}

            response = ai_pd_service.analyze_creator_performance(
                user=user,
                channels=list(channels),
                snapshots=snapshot_dict,
                question=question
            )

        elif user.role in [UserRole.MANAGER, UserRole.ADMIN]:
            # Manager asking about their portfolio
            links = session.exec(
                select(ManagerCreatorLink)
                .where(ManagerCreatorLink.manager_id == user.id)
                .where(ManagerCreatorLink.approved == True)
            ).all()

            creator_ids = [link.creator_id for link in links]
            creators = session.exec(
                select(User).where(User.id.in_(creator_ids))
            ).all() if creator_ids else []

            # Get all channels and snapshots
            all_channels: Dict[int, List[ChannelAccount]] = {}
            all_snapshots: Dict[int, Dict[int, Dict]] = {}

            for creator in creators:
                channels = session.exec(
                    select(ChannelAccount)
                    .where(ChannelAccount.owner_id == creator.id)
                    .options(selectinload(ChannelAccount.credential))
                ).all()
                all_channels[creator.id] = list(channels)
                snapshots = fetch_channel_snapshots(channels)
                all_snapshots[creator.id] = snapshots

            response = ai_pd_service.analyze_manager_portfolio(
                session=session,
                manager=user,
                creators=list(creators),
                all_channels=all_channels,
                all_snapshots=all_snapshots,
                question=question
            )

        else:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")

        return {
            "success": True,
            "question": question,
            "answer": response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 분석 중 오류가 발생했습니다: {str(e)}")
