"""
AI 설정 관리 라우터

AI 시스템 프롬프트 및 API 키 관리
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ...database import get_session
from ...dependencies import require_roles
from ...models import (
    ActivityLog,
    ManagerAPIKey,
    User,
    UserRole,
)

router = APIRouter()


@router.post("/manager/api-key/save")
def save_gemini_api_key(
    request: Request,
    api_key: str = Form(...),
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """Gemini API 키 저장 (암호화)"""
    existing_key = session.exec(
        select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)
    ).first()

    if existing_key:
        existing_key.api_key = api_key
        session.add(existing_key)
    else:
        new_key = ManagerAPIKey(manager_id=user.id)
        new_key.api_key = api_key
        session.add(new_key)

    session.add(
        ActivityLog(
            user_id=user.id,
            action="api_key_save",
            details="gemini_api_key",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/manager/dashboard?api_key=saved",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/manager/api-key/delete")
def delete_gemini_api_key(
    request: Request,
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """Gemini API 키 삭제"""
    existing_key = session.exec(
        select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)
    ).first()

    if existing_key:
        session.delete(existing_key)
        session.add(
            ActivityLog(
                user_id=user.id,
                action="api_key_delete",
                details="gemini_api_key",
            )
        )
        session.commit()

    return RedirectResponse(
        url="/manager/dashboard?api_key=deleted",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/super-admin/ai/system-prompt")
def update_ai_system_prompt(
    request: Request,
    system_prompt: str = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """AI 시스템 프롬프트 업데이트"""
    from ...services.ai.ai_pd_service import AIPDService

    AIPDService.set_system_prompt(system_prompt.strip())

    session.add(
        ActivityLog(
            user_id=user.id,
            action="ai_system_prompt_update",
            details=f"length={len(system_prompt)}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?ai_prompt=updated",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/super-admin/ai/reset-prompt")
def reset_ai_system_prompt(
    request: Request,
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """AI 시스템 프롬프트 초기화"""
    from ...services.ai.ai_pd_service import AIPDService

    AIPDService.reset_system_prompt()

    session.add(
        ActivityLog(
            user_id=user.id,
            action="ai_system_prompt_reset",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?ai_prompt=reset",
        status_code=status.HTTP_303_SEE_OTHER,
    )
