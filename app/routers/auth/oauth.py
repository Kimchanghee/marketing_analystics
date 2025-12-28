"""
OAuth 소셜 로그인 라우터

Google, Apple 등 소셜 로그인 처리
"""

from __future__ import annotations

import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jose import jwt as jose_jwt
from sqlmodel import Session, select

from ...auth import auth_manager
from ...config import get_settings
from ...database import get_session
from ...models import (
    ActivityLog,
    SocialAccount,
    SocialProvider,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ...services.social.social_auth import social_auth_service
from ...services.social.social_oauth import (
    OAuthError,
    SocialOAuthNotConfigured,
    get_oauth_client,
)

from .helpers import (
    determine_locale,
    resolve_role,
    social_error_redirect,
    is_safe_redirect_url,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """OAuth state용 토큰 생성"""
    settings = get_settings()
    expire = datetime.utcnow() + expires_delta
    to_encode = data.copy()
    to_encode["exp"] = expire
    return jose_jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """OAuth state 토큰 디코딩"""
    settings = get_settings()
    try:
        return jose_jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jose_jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token"
        ) from e


async def fetch_social_profile(
    provider: str,
    client,
    token: Dict[str, Any],
    request: Request,
    form_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """소셜 프로바이더에서 사용자 프로필 가져오기"""
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


def upsert_social_user(
    *,
    session: Session,
    provider: SocialProvider,
    provider_user_id: str,
    email: str,
    name: Optional[str],
    role: UserRole,
    locale: str,
) -> User:
    """소셜 사용자 생성 또는 업데이트"""
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
    """소셜 OAuth 시작"""
    locale = determine_locale(request)
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

    role = resolve_role(role_value)
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
    """소셜 OAuth 콜백 처리"""
    form_data: Optional[Dict[str, Any]] = None
    if request.method == "POST":
        form = await request.form()
        form_data = dict(form)
        request._form = form

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
            except (jose_jwt.JWTError, HTTPException) as jwt_err:
                logger.debug(f"Failed to decode state cookie: {jwt_err}")
            except Exception as exc:
                logger.warning(f"Unexpected error decoding OAuth state cookie: {exc}")
        return social_error_redirect(origin, locale, "social_auth_failed")

    state_value = request.query_params.get("state")
    if not state_value and form_data:
        state_value = form_data.get("state")
    if not state_value:
        state_value = request.cookies.get("oauth_state")

    if not state_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_state")

    state_cookie = request.cookies.get("oauth_state")
    if state_cookie and state_cookie != state_value:
        return social_error_redirect("/login", "ko", "invalid_state")

    try:
        state_payload = decode_token(state_value)
    except HTTPException:
        return social_error_redirect("/login", "ko", "invalid_state")

    locale = state_payload.get("locale", "ko")
    origin = state_payload.get("origin", "/login")
    action = state_payload.get("action", "login")
    next_url = state_payload.get("next")
    role = resolve_role(state_payload.get("role"))
    link_user_id = state_payload.get("link_user_id")

    profile = await fetch_social_profile(provider, client, token, request, form_data)
    provider_user_id = profile.get("id")
    email = profile.get("email")
    name = profile.get("name")

    if not provider_user_id:
        return social_error_redirect(origin, locale, "profile_missing")
    if not email:
        return social_error_redirect(origin, locale, "email_required")

    try:
        provider_enum = SocialProvider(provider)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")

    # link 액션: 기존 사용자에게 소셜 계정 연동
    if action == "link" and link_user_id:
        link_user = session.exec(select(User).where(User.id == link_user_id)).first()
        if not link_user:
            return social_error_redirect("/profile", locale, "user_not_found")

        # 이미 다른 사용자가 사용 중인 소셜 계정인지 확인
        existing_account = social_auth_service.find_account(
            session, provider_enum, str(provider_user_id)
        )
        if existing_account and existing_account.user_id != link_user_id:
            return social_error_redirect("/profile", locale, "social_account_in_use")

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
                return social_error_redirect("/profile", locale, "social_account_in_use")

        session.add(ActivityLog(user_id=link_user.id, action=f"link_{provider_enum.value}"))
        session.commit()

        response = RedirectResponse(
            url="/profile?social=linked", status_code=status.HTTP_303_SEE_OTHER
        )
        response.delete_cookie("oauth_state")
        return response

    # 일반 로그인/가입 흐름
    user = upsert_social_user(
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
    if next_url and is_safe_redirect_url(next_url):
        redirect_target = next_url
    elif user.role == UserRole.MANAGER:
        redirect_target = "/manager/dashboard"
    else:
        redirect_target = "/dashboard"

    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(response, auth_token)
    response.delete_cookie("oauth_state")

    return response
