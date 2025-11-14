"""AI PD (Personal Development) Router

Provides AI-powered analysis and feedback for creators and managers.
This is a PREMIUM feature that requires PRO or ENTERPRISE subscription.

Note: The /ai-pd dashboard route has been removed.
AI PD features are now fully integrated into the creator and manager dashboards.
"""
from typing import Dict, List

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import selectinload
from sqlmodel import select

from ..database import get_session
from ..dependencies import get_current_user, check_feature_access
from ..models import (
    ChannelAccount,
    ManagerCreatorLink,
    User,
    UserRole,
)
from ..services.ai_pd_service import (
    ai_pd_service,
    APIKeyNotConfiguredError,
    AIGenerationError,
)
from ..services.social_fetcher import fetch_channel_snapshots

router = APIRouter()


# /ai-pd 대시보드는 제거됨 - AI PD 기능은 개인/기업 대시보드에 통합되어 있습니다.


@router.post("/ai-pd/ask")
def ask_ai_pd(
    request: Request,
    question: str = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
    _feature_access: bool = Depends(check_feature_access("ai_pd"))
):
    """Ask AI PD a question about performance and get insights (PRO+ subscription required)"""
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

    except APIKeyNotConfiguredError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI 서비스가 구성되지 않았습니다: {str(e)}"
        )
    except AIGenerationError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI 분석 서비스 오류: {str(e)}"
        )
    except HTTPException:
        # Re-raise existing HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 분석 중 예기치 않은 오류가 발생했습니다: {str(e)}"
        )
