"""
회원가입 라우터

이메일 회원가입 및 소셜 회원가입 처리
"""

from __future__ import annotations

import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import Session, select

from ...auth import auth_manager
from ...database import get_session
from ...models import (
    ActivityLog,
    SocialProvider,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ...services.email.email_verification import email_verification_service
from ...services.localization import translator
from ...services.social.social_auth import social_auth_service

from .helpers import determine_locale, template_context

router = APIRouter()


@router.get("/signup")
def signup_page(request: Request):
    """회원가입 페이지 표시"""
    locale = determine_locale(request)
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
        "auth/signup.html", template_context(request, locale, strings, context)
    )


@router.post("/signup/request-code")
def request_signup_code(
    email: EmailStr = Form(...),
    locale: str = Form("ko"),
    origin: str | None = Form(None),
):
    """이메일 인증 코드 요청"""
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
    """이메일 회원가입 처리"""
    strings = translator.load_locale(locale)

    # 이메일 인증코드 검증
    if not email_verification_service.verify_code(email, verification_code):
        return request.app.state.templates.TemplateResponse(
            "auth/signup.html",
            template_context(
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
            "auth/signup.html",
            template_context(
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
            "auth/signup.html",
            template_context(
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
            "auth/signup.html",
            template_context(
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
    """소셜 회원가입 처리"""
    strings = translator.load_locale(locale)
    try:
        provider_enum = SocialProvider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_provider") from exc

    if provider_enum not in social_auth_service.get_supported_providers():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unsupported_provider")

    if privacy_agreement != "on" or guidance_agreement != "on":
        return request.app.state.templates.TemplateResponse(
            "auth/signup.html",
            template_context(
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
            "auth/signup.html",
            template_context(
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
            "auth/signup.html",
            template_context(
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
                "auth/signup.html",
                template_context(
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
