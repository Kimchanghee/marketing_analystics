from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import Session, select
from jose import jwt as jose_jwt

from ..auth import auth_manager
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
            except (TypeError, ValueError):
                user_blob = {}
            name_data = user_blob.get("name") or {}
            first_name = name_data.get("firstName")
            last_name = name_data.get("lastName")
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
async def start_social_oauth(provider: str, request: Request):
    locale = _determine_locale(request)
    action = request.query_params.get("action", "login")
    origin = request.query_params.get("origin")
    role_value = request.query_params.get("role", UserRole.CREATOR.value)
    next_url = request.query_params.get("next")

    try:
        client = get_oauth_client(provider)
    except SocialOAuthNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    role = _resolve_role(role_value)
    state_payload = {
        "provider": provider,
        "action": action,
        "role": role.value,
        "origin": origin or ("/signup" if action == "signup" else "/login"),
        "locale": locale,
        "next": next_url,
    }
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
    except OAuthError:
        state_cookie = request.cookies.get("oauth_state")
        locale = "ko"
        origin = "/login"
        if state_cookie:
            try:
                state_payload = decode_token(state_cookie)
                locale = state_payload.get("locale", locale)
                origin = state_payload.get("origin", origin)
            except Exception:
                pass
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
    redirect_target = next_url or ("/manager/dashboard" if user.role == UserRole.MANAGER else "/dashboard")
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

    # 데이터베이스 연결 확인
    try:
        user = session.exec(select(User).where(User.email == email)).first()
    except Exception as e:
        # 데이터베이스 연결 실패
        import logging
        logger = logging.getLogger(__name__)
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
                    "error": strings["auth"].get("invalid_credentials", "Invalid credentials"),
                    "providers": list(social_auth_service.get_supported_providers()),
                },
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
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

    token = auth_manager.create_access_token(user.email)
    session.add(ActivityLog(user_id=user.id, action="login"))
    session.commit()

    # SUPER_ADMIN 사용자는 로그인 후 슈퍼 관리자 콘솔로 이동
    # admin_token 파라미터를 자동으로 부여해 추가 인증 없이 접근 가능
    settings = get_settings()

    if user.role == UserRole.SUPER_ADMIN:
        redirect_to = f"/super-admin?admin_token={settings.super_admin_access_token}"
    elif user.role == UserRole.MANAGER:
        redirect_to = "/manager/dashboard"
    else:
        redirect_to = "/dashboard"

    redirect_response = RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(redirect_response, token)
    return redirect_response


@router.post("/login/social")
def social_login(
    request: Request,
    provider: str = Form(...),
    provider_user_id: str = Form(...),
    locale: str = Form("ko"),
    session: Session = Depends(get_session),
):
    strings = translator.load_locale(locale)
    try:
        provider_enum = SocialProvider(provider)
    except ValueError as exc:  # pragma: no cover - validation guard
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_provider") from exc

    if provider_enum not in social_auth_service.get_supported_providers():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")

    account = social_auth_service.find_account(session, provider_enum, provider_user_id)
    if not account:
        redirect_url = f"/login?lang={locale}&social_error=social_account_not_found"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    user = session.exec(select(User).where(User.id == account.user_id)).first()
    if not user or not user.is_active:
        redirect_url = f"/login?lang={locale}&social_error=account_inactive"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    token = auth_manager.create_access_token(user.email)
    session.add(ActivityLog(user_id=user.id, action=f"social_login_{provider_enum.value}"))
    session.commit()

    # SUPER_ADMIN 사용자는 로그인 후 슈퍼 관리자 콘솔로 이동
    # admin_token 파라미터를 자동으로 부여해 추가 인증 없이 접근 가능
    settings = get_settings()

    if user.role == UserRole.SUPER_ADMIN:
        redirect_to = f"/super-admin?admin_token={settings.super_admin_access_token}"
    elif user.role == UserRole.MANAGER:
        redirect_to = "/manager/dashboard"
    else:
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
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
    session: Session = Depends(get_session),
):
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


@router.post("/social/link")
def link_social(
    user: User = Depends(get_current_user),
    provider: str = Form(...),
    provider_user_id: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        provider_enum = SocialProvider(provider)
    except ValueError as exc:  # pragma: no cover - validation guard
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_provider") from exc

    if provider_enum not in social_auth_service.get_supported_providers():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")

    db_user = session.exec(select(User).where(User.id == user.id)).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

    try:
        social_auth_service.link_account(
            session=session,
            user=db_user,
            provider=provider_enum,
            provider_user_id=provider_user_id,
        )
    except ValueError:
        redirect = RedirectResponse(
            url="/profile?social_error=social_account_in_use", status_code=status.HTTP_303_SEE_OTHER
        )
        return redirect

    session.commit()
    redirect = RedirectResponse(url="/profile?social=linked", status_code=status.HTTP_303_SEE_OTHER)
    return redirect


@router.post("/logout")
def logout():
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.clear_login_cookie(redirect_response)
    return redirect_response

