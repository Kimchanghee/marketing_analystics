"""
로그인/로그아웃 라우터

사용자 로그인, 로그아웃 처리
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from ...auth import auth_manager
from ...database import get_session
from ...models import ActivityLog, User, UserRole
from ...services.localization import translator
from ...services.login_throttle import login_throttle_service
from ...services.social_auth import social_auth_service

from .helpers import determine_locale, template_context, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    """로그인 페이지 표시"""
    locale = determine_locale(request)
    strings = translator.load_locale(locale)
    signup_status = request.query_params.get("signup")
    success_key = request.query_params.get("success")
    social_error_key = request.query_params.get("social_error")
    social_success_key = request.query_params.get("social_success")
    recovery_key = request.query_params.get("recovery")

    if signup_status == "success":
        success_message = strings["auth"].get("signup_success")
    elif success_key:
        success_message = strings["auth"].get(success_key)
    else:
        success_message = None

    context = {
        "success": success_message,
        "providers": list(social_auth_service.get_supported_providers()),
        "social_error": strings["auth"].get(social_error_key) if social_error_key else None,
        "social_success": strings["auth"].get(social_success_key) if social_success_key else None,
        "recovery_message": strings["auth"].get(recovery_key) if recovery_key else None,
    }
    return request.app.state.templates.TemplateResponse(
        "auth/login.html", template_context(request, locale, strings, context)
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    origin: str | None = Form(None),
    session: Session = Depends(get_session),
):
    """로그인 처리"""
    locale = determine_locale(request)
    strings = translator.load_locale(locale)
    client_ip = get_client_ip(request)

    # 로그인 시도 제한 확인
    is_locked, remaining_seconds = login_throttle_service.is_locked_out(email, client_ip)
    if is_locked:
        remaining_minutes = (remaining_seconds // 60) + 1
        error_msg = strings["auth"].get(
            "too_many_attempts",
            f"Too many login attempts. Please try again in {remaining_minutes} minutes."
        ).format(minutes=remaining_minutes) if "{minutes}" in strings["auth"].get("too_many_attempts", "") else f"로그인 시도가 너무 많습니다. {remaining_minutes}분 후에 다시 시도해주세요."

        if origin == "landing":
            redirect_url = f"/?lang={locale}&login_error=too_many_attempts"
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            template_context(
                request,
                locale,
                strings,
                {
                    "error": error_msg,
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # 데이터베이스 연결 확인
    try:
        user = session.exec(select(User).where(User.email == email)).first()
    except Exception as e:
        logger.error(f"Database connection failed during login: {e}", exc_info=True)
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            template_context(
                request,
                locale,
                strings,
                {
                    "error": "서버 데이터베이스 연결 오류가 발생했습니다. 관리자에게 문의하세요.",
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not user or not auth_manager.verify_password(password, user.hashed_password):
        # 보안 감사 로깅 - 로그인 실패
        reason = "user_not_found" if not user else "invalid_password"
        logger.warning(
            f"Login failed: email={email} ip={client_ip} reason={reason}"
        )

        # 로그인 실패 기록
        is_now_locked, remaining_attempts, lockout_secs = login_throttle_service.record_failed_attempt(email, client_ip)

        error_msg = strings["auth"].get("invalid_credentials", "Invalid credentials")
        if is_now_locked:
            lockout_minutes = (lockout_secs // 60)
            error_msg = f"로그인 시도가 너무 많습니다. {lockout_minutes}분 후에 다시 시도해주세요."
        elif remaining_attempts <= 2:
            error_msg = f"{error_msg} (남은 시도: {remaining_attempts}회)"

        if origin == "landing":
            redirect_url = f"/?lang={locale}&login_error=invalid_credentials"
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            template_context(
                request,
                locale,
                strings,
                {
                    "error": error_msg,
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS if is_now_locked else status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_active:
        if origin == "landing":
            redirect_url = f"/?lang={locale}&login_error=account_inactive"
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("account_inactive", "Account is inactive"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not user.is_email_verified:
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("email_not_verified"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if not user.password_login_enabled:
        return request.app.state.templates.TemplateResponse(
            "auth/login.html",
            template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("password_login_disabled"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # 로그인 성공 - 시도 기록 초기화
    login_throttle_service.record_successful_login(email, client_ip)

    # 보안 감사 로깅 - 로그인 성공
    logger.info(
        f"Login successful: email={email} ip={client_ip} user_id={user.id} role={user.role.value}"
    )

    token = auth_manager.create_access_token(user.email)
    session.add(ActivityLog(user_id=user.id, action="login"))
    session.commit()

    # 역할별 리다이렉트
    if user.role == UserRole.MANAGER:
        redirect_to = "/manager/dashboard"
    else:
        redirect_to = "/dashboard"

    redirect_response = RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(redirect_response, token)
    return redirect_response


@router.post("/logout")
def logout():
    """로그아웃 처리"""
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.clear_login_cookie(redirect_response)
    return redirect_response
