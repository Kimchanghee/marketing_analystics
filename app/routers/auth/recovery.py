"""
계정 복구 라우터

비밀번호 재설정, 사용자명 찾기
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import Session, select

from ...database import get_session
from ...models import User
from ...services.account_recovery import account_recovery_service
from ...services.localization import translator

from .helpers import determine_locale, template_context

router = APIRouter()


@router.get("/recover")
def recovery_page(request: Request):
    """계정 복구 페이지 표시"""
    locale = determine_locale(request)
    strings = translator.load_locale(locale)
    success_key = request.query_params.get("success")
    error_key = request.query_params.get("error")
    context = {
        "success": strings["auth"].get(success_key) if success_key else None,
        "error": strings["auth"].get(error_key) if error_key else None,
    }
    return request.app.state.templates.TemplateResponse(
        "auth/recovery.html", template_context(request, locale, strings, context)
    )


@router.post("/recover/username")
def recover_username(
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
):
    """사용자명 찾기"""
    if account_recovery_service.remind_username(email):
        redirect_url = f"/recover?lang={locale}&success=username_sent"
    else:
        redirect_url = f"/recover?lang={locale}&error=account_not_found"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/recover/password")
def recover_password(
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
    session: Session = Depends(get_session),
):
    """비밀번호 재설정 토큰 요청"""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        redirect_url = f"/recover?lang={locale}&error=account_not_found"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    account_recovery_service.create_reset_token(user)
    redirect_url = f"/recover?lang={locale}&success=password_token_sent"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/recover/password/confirm")
def confirm_password_reset(
    email: EmailStr = Form(...),
    token: str = Form(...),
    new_password: str = Form(...),
    locale: str = Form("ko"),
    session: Session = Depends(get_session),
):
    """비밀번호 재설정 확인"""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        redirect_url = f"/recover?lang={locale}&error=account_not_found"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    if not account_recovery_service.reset_password(user, token, new_password):
        redirect_url = f"/recover?lang={locale}&error=invalid_token"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    redirect_url = f"/login?lang={locale}&success=password_reset"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
