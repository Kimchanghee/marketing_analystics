"""
슈퍼 관리자 대시보드 라우터

슈퍼 관리자 메인 대시보드 표시
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlmodel import select

from ...config import get_settings
from ...database import get_session
from ...dependencies import require_roles
from ...models import (
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ...services.localization import translator
from ...services.email.super_admin_email import (
    EmailConfigurationError,
    EmailReceiveError,
    EmailServiceError,
    SuperAdminEmailService,
)

router = APIRouter()


@router.get("/super-admin")
def super_admin_dashboard(
    request: Request,
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """슈퍼 관리자 대시보드"""
    locale = user.locale
    strings = translator.load_locale(locale)

    # 페이지네이션 (기본 50개씩)
    page = int(request.query_params.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    # 전체 사용자 수 조회
    total_users = session.exec(select(func.count(User.id))).first() or 0

    # 페이지별 사용자 조회 (성능 최적화)
    users = session.exec(
        select(User)
        .order_by(User.created_at.desc())
        .limit(per_page)
        .offset(offset)
    ).all()

    # 구독 정보는 현재 페이지 사용자만 조회
    user_ids = [u.id for u in users]
    subscriptions = session.exec(
        select(Subscription).where(Subscription.user_id.in_(user_ids))
    ).all() if user_ids else []

    # 회원 구분: 기업(MANAGER) / 개인(CREATOR)
    business_users = [u for u in users if u.role == UserRole.MANAGER or u.role == UserRole.ADMIN]
    personal_users = [u for u in users if u.role == UserRole.CREATOR]

    # 페이지 정보
    total_pages = (total_users + per_page - 1) // per_page

    # 최근 결제 내역 (100개)
    recent_payments = session.exec(
        select(Payment).order_by(Payment.created_at.desc()).limit(100)
    ).all()

    # 결제 통계
    total_revenue = session.exec(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.PAID)
    ).first() or 0

    user_lookup = {u.id: u for u in users}

    # AI API 키 확인
    settings = get_settings()
    gemini_api_key_set = hasattr(settings, 'gemini_api_key') and settings.gemini_api_key and settings.gemini_api_key != ""

    # AI PD 시스템 프롬프트
    from ...services.ai.ai_pd_service import AIPDService
    ai_system_prompt = AIPDService.get_system_prompt()

    # 이메일 서비스
    email_inbox = []
    email_sent = []
    email_error = None
    email_service_configured = False
    email_last_refreshed = None

    try:
        email_service_configured = SuperAdminEmailService.is_configured(settings)
        if email_service_configured:
            email_service = SuperAdminEmailService(settings)
            email_inbox = email_service.fetch_inbox(limit=10)
            email_sent = email_service.fetch_sent(limit=10)
            email_last_refreshed = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    except (EmailConfigurationError, EmailReceiveError, EmailServiceError) as exc:
        email_error = str(exc)

    return request.app.state.templates.TemplateResponse(
        "admin/super_admin.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "users": users,
            "business_users": business_users,
            "personal_users": personal_users,
            "subscriptions": {subscription.user_id: subscription for subscription in subscriptions},
            "recent_payments": recent_payments,
            "total_revenue": total_revenue,
            "payments": list(recent_payments),
            "logs": [],
            "roles": list(UserRole),
            "tiers": list(SubscriptionTier),
            "payment_statuses": list(PaymentStatus),
            "user_lookup": user_lookup,
            "gemini_api_key_set": gemini_api_key_set,
            "ai_system_prompt": ai_system_prompt,
            "email_service_configured": email_service_configured,
            "email_error": email_error,
            "email_inbox": email_inbox,
            "email_sent": email_sent,
            "super_admin_email": settings.super_admin_email,
            "page": page,
            "per_page": per_page,
            "total_users": total_users,
            "total_pages": total_pages,
            "email_last_refreshed": email_last_refreshed,
        },
    )
