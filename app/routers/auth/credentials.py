"""
자격증명 관리 라우터

비밀번호 설정/변경
"""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from ...auth import auth_manager
from ...database import get_session
from ...dependencies import get_current_user
from ...models import ActivityLog, User
from ...services.email_verification import email_verification_service

router = APIRouter()


@router.post("/credentials/set-password")
def set_password(
    user: User = Depends(get_current_user),
    new_password: str = Form(...),
    verification_code: str = Form(...),
    session: Session = Depends(get_session),
):
    """비밀번호 설정 (소셜 로그인 사용자용)"""
    if not email_verification_service.verify_code(user.email, verification_code):
        redirect = RedirectResponse(
            url="/profile?credentials_error=invalid_verification_code",
            status_code=status.HTTP_303_SEE_OTHER,
        )
        return redirect

    db_user = session.exec(select(User).where(User.id == user.id)).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

    db_user.hashed_password = auth_manager.hash_password(new_password)
    db_user.password_login_enabled = True
    db_user.password_set_at = datetime.utcnow()
    session.add(ActivityLog(user_id=db_user.id, action="password_set"))
    session.add(db_user)
    session.commit()
    email_verification_service.clear_code(user.email)
    redirect = RedirectResponse(
        url="/profile?credentials=updated", status_code=status.HTTP_303_SEE_OTHER
    )
    return redirect
