from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import Session, select
from jose import jwt as jose_jwt

from ..auth import auth_manager, create_access_token, decode_token

logger = logging.getLogger(__name__)
from ..config import get_settings
from ..database import get_session
from ..dependencies import get_current_user
from ..models import (
    ActivityLog,
    SocialAccount,
    SocialProvider,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ..services.account_recovery import account_recovery_service
from ..services.email_verification import email_verification_service
from ..services.localization import translator
from ..services.login_throttle import login_throttle_service
from ..services.social_auth import social_auth_service
from ..services.social_oauth import (
    OAuthError,
    SocialOAuthNotConfigured,
    get_oauth_client,
)

router = APIRouter()


def _determine_locale(request: Request) -> str:
    return getattr(request.state, "locale", request.query_params.get("lang", "ko"))


def _template_context(
    request: Request, locale: str, strings: dict, extra: dict | None = None
) -> dict:
    context = {"request": request, "locale": locale, "t": strings}
    if extra:
        context.update(extra)
    return context


def _append_query_params(url: str, params: dict[str, str | None]) -> str:
    filtered = {k: v for k, v in params.items() if v}
    if not filtered:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(filtered)}"


def _resolve_role(value: str | None) -> UserRole:
    if not value:
        return UserRole.CREATOR
    try:
        return UserRole(value)
    except ValueError:
        return UserRole.CREATOR


def _social_error_redirect(origin: str | None, locale: str, error_key: str) -> RedirectResponse:
    target = origin or "/login"
    redirect_url = _append_query_params(target, {"lang": locale, "social_error": error_key})
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("oauth_state")
    return response


async def _fetch_social_profile(
    provider: str,
    client,
    token: Dict[str, Any],
    request: Request,
    form_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile: Dict[str, Any] = {}

    if provider == "google":
        resp = await client.get("userinfo", token=token)
        profile = resp.json()
        if not profile.get("email") and token.get("id_token"):
            claims = jose_jwt.get_unverified_claims(token["id_token"])
            profile.setdefault("sub", claims.get("sub"))
            profile.setdefault("email", claims.get("email"))
            if claims.get("name"):
                profile.setdefault("name", claims.get("name"))
        return {
            "id": profile.get("sub") or profile.get("id"),
            "email": profile.get("email"),
            "name": profile.get("name")
            or " ".join(filter(None, [profile.get("given_name"), profile.get("family_name")])).strip()
            or None,
            "raw": profile,
        }

    if provider == "apple":
        claims: Dict[str, Any] = {}
        if token.get("id_token"):
            claims = jose_jwt.get_unverified_claims(token["id_token"])
        full_name: Optional[str] = None
        if form_data and form_data.get("user"):
            try:
                user_blob = json.loads(form_data.get("user"))
                # JSON 스키마 검증 - 허용된 필드만 추출
                if not isinstance(user_blob, dict):
                    user_blob = {}
            except (TypeError, ValueError, json.JSONDecodeError):
                user_blob = {}
            name_data = user_blob.get("name") if isinstance(user_blob.get("name"), dict) else {}
            first_name = str(name_data.get("firstName", ""))[:100] if name_data.get("firstName") else None
            last_name = str(name_data.get("lastName", ""))[:100] if name_data.get("lastName") else None
            full_name = " ".join(filter(None, [first_name, last_name])).strip() or None
        if not full_name and claims.get("name"):
            full_name = claims.get("name")
        return {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            "name": full_name,
            "raw": claims,
        }

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")


def _upsert_social_user(
    *,
    session: Session,
    provider: SocialProvider,
    provider_user_id: str,
    email: str,
    name: Optional[str],
    role: UserRole,
    locale: str,
) -> User:
    social_account = session.exec(
        select(SocialAccount)
        .where(SocialAccount.provider == provider)
        .where(SocialAccount.provider_user_id == provider_user_id)
    ).first()

    if social_account:
        user = session.get(User, social_account.user_id)
        if user:
            return user
        session.delete(social_account)
        session.commit()

    user = session.exec(select(User).where(User.email == email)).first()
    created_now = False
    if not user:
        hashed_password = auth_manager.hash_password(secrets.token_urlsafe(32))
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            locale=locale,
            organization=None,
            name=name or email.split("@")[0],
            is_active=True,
            is_email_verified=True,
            password_login_enabled=False,
            privacy_consent=True,
            guidance_consent=True,
            password_set_at=datetime.utcnow(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        subscription = Subscription(
            user_id=user.id,
            tier=SubscriptionTier.FREE,
            max_accounts=1,
            active=True,
        )
        session.add(subscription)
        session.add(ActivityLog(user_id=user.id, action=f"signup_social_{provider.value}"))
        session.commit()
        created_now = True
    else:
        if not user.name and name:
            user.name = name
            session.add(user)
        if not user.is_email_verified:
            user.is_email_verified = True
            session.add(user)
        session.commit()

    existing_link = session.exec(
        select(SocialAccount)
        .where(SocialAccount.provider == provider)
        .where(SocialAccount.user_id == user.id)
    ).first()
    if not existing_link:
        social_account = SocialAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            metadata_json={},
        )
        session.add(social_account)
        action = "signup" if created_now else "link"
        session.add(ActivityLog(user_id=user.id, action=f"{action}_{provider.value}"))
        session.commit()

    return user


@router.get("/oauth/{provider}")
async def start_social_oauth(
    provider: str,
    request: Request,
    session: Session = Depends(get_session),
):
    locale = _determine_locale(request)
    action = request.query_params.get("action", "login")
    origin = request.query_params.get("origin")
    role_value = request.query_params.get("role", UserRole.CREATOR.value)
    next_url = request.query_params.get("next")

    # link 액션은 로그인된 사용자만 가능
    link_user_id = None
    if action == "link":
        token = request.cookies.get("session")
        if not token:
            return RedirectResponse(
                url="/login?social_error=login_required",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        try:
            email = auth_manager.decode_token(token)
            user = session.exec(select(User).where(User.email == email)).first()
            if user:
                link_user_id = user.id
            else:
                return RedirectResponse(
                    url="/login?social_error=login_required",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
        except Exception:
            return RedirectResponse(
                url="/login?social_error=login_required",
                status_code=status.HTTP_303_SEE_OTHER,
            )

    try:
        client = get_oauth_client(provider)
    except SocialOAuthNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    role = _resolve_role(role_value)
    state_payload = {
        "provider": provider,
        "action": action,
        "role": role.value,
        "origin": origin or ("/profile" if action == "link" else ("/signup" if action == "signup" else "/login")),
        "locale": locale,
        "next": next_url,
    }
    if link_user_id:
        state_payload["link_user_id"] = link_user_id
    state_token = create_access_token(state_payload, expires_delta=timedelta(minutes=10))
    redirect_uri = request.url_for("social_oauth_callback", provider=provider)

    try:
        response = await client.authorize_redirect(request, redirect_uri, state=state_token)
    except OAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    settings = get_settings()
    response.set_cookie(
        "oauth_state",
        state_token,
        max_age=600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    return response


@router.api_route("/oauth/{provider}/callback", methods=["GET", "POST"])
async def social_oauth_callback(
    provider: str,
    request: Request,
    session: Session = Depends(get_session),
):
    form_data: Optional[Dict[str, Any]] = None
    if request.method == "POST":
        form = await request.form()
        form_data = dict(form)
        # Starlette caches form data so downstream consumers can reuse it
        request._form = form  # type: ignore[attr-defined]

    try:
        client = get_oauth_client(provider)
    except SocialOAuthNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    try:
        token = await client.authorize_access_token(request)
    except OAuthError as e:
        logger.warning(f"OAuth authorization failed: {e}")
        state_cookie = request.cookies.get("oauth_state")
        locale = "ko"
        origin = "/login"
        if state_cookie:
            try:
                state_payload = decode_token(state_cookie)
                locale = state_payload.get("locale", locale)
                origin = state_payload.get("origin", origin)
            except jose_jwt.JWTError as jwt_err:
                logger.debug(f"Failed to decode state cookie (expected if expired): {jwt_err}")
            except Exception as exc:
                logger.warning(f"Unexpected error decoding OAuth state cookie: {exc}")
        return _social_error_redirect(origin, locale, "social_auth_failed")

    state_value = request.query_params.get("state")
    if not state_value and form_data:
        state_value = form_data.get("state")
    if not state_value:
        state_value = request.cookies.get("oauth_state")

    if not state_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_state")

    state_cookie = request.cookies.get("oauth_state")
    if state_cookie and state_cookie != state_value:
        return _social_error_redirect("/login", "ko", "invalid_state")

    try:
        state_payload = decode_token(state_value)
    except HTTPException:
        return _social_error_redirect("/login", "ko", "invalid_state")

    locale = state_payload.get("locale", "ko")
    origin = state_payload.get("origin", "/login")
    action = state_payload.get("action", "login")
    next_url = state_payload.get("next")
    role = _resolve_role(state_payload.get("role"))
    link_user_id = state_payload.get("link_user_id")

    profile = await _fetch_social_profile(provider, client, token, request, form_data)
    provider_user_id = profile.get("id")
    email = profile.get("email")
    name = profile.get("name")

    if not provider_user_id:
        return _social_error_redirect(origin, locale, "profile_missing")
    if not email:
        return _social_error_redirect(origin, locale, "email_required")

    try:
        provider_enum = SocialProvider(provider)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")

    # link 액션: 기존 사용자에게 소셜 계정 연동
    if action == "link" and link_user_id:
        link_user = session.exec(select(User).where(User.id == link_user_id)).first()
        if not link_user:
            return _social_error_redirect("/profile", locale, "user_not_found")

        # 이미 다른 사용자가 사용 중인 소셜 계정인지 확인
        existing_account = social_auth_service.find_account(
            session, provider_enum, str(provider_user_id)
        )
        if existing_account and existing_account.user_id != link_user_id:
            return _social_error_redirect("/profile", locale, "social_account_in_use")

        # 이미 연동된 경우 스킵
        if not existing_account:
            try:
                social_auth_service.link_account(
                    session=session,
                    user=link_user,
                    provider=provider_enum,
                    provider_user_id=str(provider_user_id),
                )
                session.commit()
            except ValueError:
                return _social_error_redirect("/profile", locale, "social_account_in_use")

        session.add(ActivityLog(user_id=link_user.id, action=f"link_{provider_enum.value}"))
        session.commit()

        response = RedirectResponse(
            url="/profile?social=linked", status_code=status.HTTP_303_SEE_OTHER
        )
        response.delete_cookie("oauth_state")
        return response

    # 일반 로그인/가입 흐름
    user = _upsert_social_user(
        session=session,
        provider=provider_enum,
        provider_user_id=str(provider_user_id),
        email=email,
        name=name,
        role=role,
        locale=locale,
    )

    session.add(ActivityLog(user_id=user.id, action=f"login_social_{provider_enum.value}"))
    session.commit()

    auth_token = auth_manager.create_access_token(user.email)

    # Role별 자동 리다이렉트 (안전한 URL만 허용)
    if next_url and _is_safe_redirect_url(next_url):
        redirect_target = next_url
    elif user.role == UserRole.MANAGER:
        redirect_target = "/manager/dashboard"
    else:
        redirect_target = "/dashboard"

    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(response, auth_token)
    response.delete_cookie("oauth_state")

    return response


@router.get("/login")
def login_page(request: Request):
    locale = _determine_locale(request)
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
        "login.html", _template_context(request, locale, strings, context)
    )


def _get_client_ip(request: Request) -> str:
    """Get client IP address from request, handling proxy headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _is_safe_redirect_url(url: str | None) -> bool:
    """Validate that redirect URL is safe (internal path only).

    Prevents open redirect attacks by only allowing:
    - None/empty (safe - will use default)
    - Relative paths starting with /
    - No protocol or domain specification
    """
    if not url:
        return True

    # Must start with / for relative path
    if not url.startswith("/"):
        return False

    # Block protocol-relative URLs (//example.com)
    if url.startswith("//"):
        return False

    # Block URLs with protocols
    if "://" in url:
        return False

    # Block JavaScript URLs
    if url.lower().startswith("javascript:"):
        return False

    return True


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    origin: str | None = Form(None),
    session: Session = Depends(get_session),
):
    locale = _determine_locale(request)
    strings = translator.load_locale(locale)
    client_ip = _get_client_ip(request)

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
            "login.html",
            _template_context(
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
        # 데이터베이스 연결 실패
        logger.error(f"Database connection failed during login: {e}", exc_info=True)

        return request.app.state.templates.TemplateResponse(
            "login.html",
            _template_context(
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
            "login.html",
            _template_context(
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
            "login.html",
            _template_context(
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
            "login.html",
            _template_context(
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
            "login.html",
            _template_context(
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
    # SUPER_ADMIN은 /dashboard로 이동 (모든 페이지 접근 가능)
    # /super-admin은 수동으로 접속해야 함 (admin_token 필요)
    if user.role == UserRole.MANAGER:
        redirect_to = "/manager/dashboard"
    else:
        # CREATOR, SUPER_ADMIN 등은 모두 /dashboard로
        redirect_to = "/dashboard"

    redirect_response = RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(redirect_response, token)
    return redirect_response


@router.get("/signup")
def signup_page(request: Request):
    locale = _determine_locale(request)
    strings = translator.load_locale(locale)
    code_status = request.query_params.get("code")
    error_key = request.query_params.get("signup_error")
    success_key = request.query_params.get("signup_success")
    selected_provider = request.query_params.get("provider")
    if selected_provider:
        try:
            provider_enum = SocialProvider(selected_provider)
        except ValueError:
            selected_provider = None
        else:
            selected_provider = provider_enum.value
    context = {
        "providers": list(social_auth_service.get_supported_providers()),
        "code_status": strings["auth"].get("verification_sent") if code_status == "sent" else None,
        "error": strings["auth"].get(error_key) if error_key else None,
        "success": strings["auth"].get(success_key) if success_key else None,
        "default_role": request.query_params.get("role", UserRole.CREATOR.value),
        "selected_provider": selected_provider,
    }
    return request.app.state.templates.TemplateResponse(
        "signup.html", _template_context(request, locale, strings, context)
    )


@router.post("/signup/request-code")
def request_signup_code(
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
    origin: str | None = Form(None),
):
    email_verification_service.request_code(email, locale=locale)
    if origin == "landing":
        redirect_url = f"/?lang={locale}&signup_success=verification_sent"
    elif origin == "profile":
        redirect_url = "/profile?code=sent"
    else:
        redirect_url = f"/signup?lang={locale}&code=sent"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/signup")
def signup(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...),
    verification_code: str = Form(...),
    role: UserRole = Form(UserRole.CREATOR),
    locale: str = Form("ko"),
    organization: str | None = Form(None),
    name: str = Form(...),
    privacy_agreement: str | None = Form(None),
    guidance_agreement: str | None = Form(None),
    origin: str | None = Form(None),
    session: Session = Depends(get_session),
):
    strings = translator.load_locale(locale)

    # 이메일 인증코드 검증
    if not email_verification_service.verify_code(email, verification_code):
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("invalid_verification_code", "Invalid verification code"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if privacy_agreement != "on" or guidance_agreement != "on":
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": "개인정보 및 이용약관에 동의해야 합니다.",
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    cleaned_name = name.strip()
    if not cleaned_name:
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": "이름을 입력해주세요.",
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        if origin == "landing":
            redirect_url = f"/?lang={locale}&signup_error=email_exists&role={role.value}"
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("email_exists", "Email already registered"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    hashed_password = auth_manager.hash_password(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        locale=locale,
        organization=organization,
        name=cleaned_name,
        is_email_verified=True,
        password_login_enabled=True,
        privacy_consent=True,
        guidance_consent=True,
        password_set_at=datetime.utcnow(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE, max_accounts=1)
    session.add(subscription)
    session.add(ActivityLog(user_id=user.id, action="signup"))
    session.commit()
    email_verification_service.clear_code(email)
    success_key = "signup_success"
    if origin == "landing":
        redirect_url = f"/?lang={locale}&signup_success={success_key}"
    else:
        redirect_url = f"/login?signup=success&lang={locale}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/signup/social")
def social_signup(
    request: Request,
    provider: str = Form(...),
    provider_user_id: str | None = Form(None),
    email: EmailStr = Form(...),
    name: str = Form(...),
    locale: str = Form("ko"),
    role: UserRole = Form(UserRole.CREATOR),
    organization: str | None = Form(None),
    password: str | None = Form(None),
    verification_code: str = Form(...),
    privacy_agreement: str | None = Form(None),
    guidance_agreement: str | None = Form(None),
    origin: str | None = Form(None),
    session: Session = Depends(get_session),
):
    strings = translator.load_locale(locale)
    try:
        provider_enum = SocialProvider(provider)
    except ValueError as exc:  # pragma: no cover - validation guard
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_provider") from exc

    if provider_enum not in social_auth_service.get_supported_providers():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")

    if privacy_agreement != "on" or guidance_agreement != "on":
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("consent_required"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    cleaned_name = name.strip()
    if not cleaned_name:
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("name_required"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not email_verification_service.verify_code(email, verification_code):
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            _template_context(
                request,
                locale,
                strings,
                {
                    "error": strings["auth"].get("invalid_verification_code"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    derived_provider_user_id = (
        provider_user_id.strip()
        if provider_user_id and provider_user_id.strip()
        else f"{provider_enum.value}:{email.strip().lower()}"
    )

    existing_user = session.exec(select(User).where(User.email == email)).first()
    if existing_user:
        try:
            social_auth_service.link_account(
                session=session,
                user=existing_user,
                provider=provider_enum,
                provider_user_id=derived_provider_user_id,
            )
        except ValueError:
            return request.app.state.templates.TemplateResponse(
                "signup.html",
                _template_context(
                    request,
                    locale,
                    strings,
                    {
                        "error": strings["auth"].get("social_account_in_use"),
                        "providers": list(social_auth_service.get_supported_providers()),
                    },
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        existing_user.is_email_verified = True
        existing_user.name = existing_user.name or cleaned_name
        existing_user.privacy_consent = True
        existing_user.guidance_consent = True
        if password:
            existing_user.hashed_password = auth_manager.hash_password(password)
            existing_user.password_login_enabled = True
            existing_user.password_set_at = datetime.utcnow()
        session.add(ActivityLog(user_id=existing_user.id, action="social_link_signup"))
        session.commit()
        email_verification_service.clear_code(email)
        redirect_url = f"/login?lang={locale}&social_success=social_signup_linked"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    generated_password = password or secrets.token_urlsafe(12)
    hashed_password = auth_manager.hash_password(generated_password)
    password_enabled = bool(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        locale=locale,
        organization=organization,
        name=cleaned_name,
        is_email_verified=True,
        password_login_enabled=password_enabled,
        privacy_consent=True,
        guidance_consent=True,
        password_set_at=datetime.utcnow() if password_enabled else None,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    social_auth_service.link_account(
        session=session,
        user=user,
        provider=provider_enum,
        provider_user_id=derived_provider_user_id,
    )
    subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE, max_accounts=1)
    session.add(subscription)
    session.add(ActivityLog(user_id=user.id, action="social_signup"))
    session.commit()
    email_verification_service.clear_code(email)

    if origin == "landing":
        redirect_url = f"/?lang={locale}&signup_success=social_signup"
    else:
        redirect_url = f"/login?lang={locale}&social_success=social_signup"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/recover")
def recovery_page(request: Request):
    locale = _determine_locale(request)
    strings = translator.load_locale(locale)
    success_key = request.query_params.get("success")
    error_key = request.query_params.get("error")
    context = {
        "success": strings["auth"].get(success_key) if success_key else None,
        "error": strings["auth"].get(error_key) if error_key else None,
    }
    return request.app.state.templates.TemplateResponse(
        "recovery.html", _template_context(request, locale, strings, context)
    )


@router.post("/recover/username")
def recover_username(
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
):
    if account_recovery_service.remind_username(email):
        redirect_url = f"/recover?lang={locale}&success=username_sent"
    else:
        redirect_url = f"/recover?lang={locale}&error=account_not_found"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/recover/password")
def recover_password(
    request: Request,
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        redirect_url = f"/recover?lang={locale}&error=account_not_found"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    base_url = str(request.base_url).rstrip("/")
    account_recovery_service.create_reset_token(user, base_url=base_url)
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
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        redirect_url = f"/recover?lang={locale}&error=account_not_found"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    if not account_recovery_service.reset_password(user, token, new_password):
        redirect_url = f"/recover?lang={locale}&error=invalid_token"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    redirect_url = f"/login?lang={locale}&success=password_reset"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/credentials/set-password")
def set_password(
    user: User = Depends(get_current_user),
    new_password: str = Form(...),
    verification_code: str = Form(...),
    session: Session = Depends(get_session),
):
    locale = user.locale
    if not email_verification_service.verify_code(user.email, verification_code):
        redirect = RedirectResponse(
            url="/profile?credentials_error=invalid_verification_code", status_code=status.HTTP_303_SEE_OTHER
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
    redirect = RedirectResponse(url="/profile?credentials=updated", status_code=status.HTTP_303_SEE_OTHER)
    return redirect


@router.post("/logout")
def logout():
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.clear_login_cookie(redirect_response)
    return redirect_response
