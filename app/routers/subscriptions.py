from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ..database import get_session, session_context
from ..dependencies import get_current_user
from ..models import Subscription, SubscriptionTier, User, ActivityLog
from ..services.localization import translator
from ..services.email.resend_email import resend_email_service
from ..config import get_settings

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# 플랜 정보 (가격, 기능 등)
PLAN_INFO = {
    SubscriptionTier.FREE: {
        "name": {"ko": "무료", "en": "Free", "ja": "無料"},
        "price": {"ko": "₩0", "en": "$0", "ja": "¥0"},
        "price_value": 0,
        "max_accounts": 1,
        "features": {
            "ko": ["채널 1개 연결", "기본 통계", "7일 데이터 보관"],
            "en": ["1 channel", "Basic analytics", "7-day data retention"],
            "ja": ["1チャンネル", "基本統計", "7日間データ保持"],
        },
    },
    SubscriptionTier.PRO: {
        "name": {"ko": "프로", "en": "Pro", "ja": "プロ"},
        "price": {"ko": "₩29,000/월", "en": "$29/mo", "ja": "¥2,900/月"},
        "price_value": 29000,
        "max_accounts": 5,
        "features": {
            "ko": ["채널 5개 연결", "고급 분석", "30일 데이터 보관", "AI 추천"],
            "en": ["5 channels", "Advanced analytics", "30-day retention", "AI recommendations"],
            "ja": ["5チャンネル", "高度な分析", "30日間データ保持", "AI推奨"],
        },
    },
    SubscriptionTier.ENTERPRISE: {
        "name": {"ko": "엔터프라이즈", "en": "Enterprise", "ja": "エンタープライズ"},
        "price": {"ko": "₩99,000/월", "en": "$99/mo", "ja": "¥9,900/月"},
        "price_value": 99000,
        "max_accounts": 20,
        "features": {
            "ko": ["채널 20개 연결", "팀 협업", "무제한 데이터", "전담 지원", "API 액세스"],
            "en": ["20 channels", "Team collaboration", "Unlimited data", "Priority support", "API access"],
            "ja": ["20チャンネル", "チームコラボ", "無制限データ", "優先サポート", "APIアクセス"],
        },
    },
}


def get_plan_info(tier: SubscriptionTier, locale: str = "ko") -> dict:
    """Get localized plan information."""
    info = PLAN_INFO.get(tier, PLAN_INFO[SubscriptionTier.FREE])
    return {
        "tier": tier.value,
        "name": info["name"].get(locale, info["name"]["en"]),
        "price": info["price"].get(locale, info["price"]["en"]),
        "price_value": info["price_value"],
        "max_accounts": info["max_accounts"],
        "features": info["features"].get(locale, info["features"]["en"]),
    }


@router.get("/pricing")
def pricing_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
):
    """결제 플랜 선택 페이지"""
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)

    # 현재 구독 정보
    current_tier = None
    if user:
        with session_context() as session:
            subscription = session.exec(
                select(Subscription).where(Subscription.user_id == user.id)
            ).first()
            current_tier = subscription.tier if subscription else SubscriptionTier.FREE

    plans = [
        get_plan_info(SubscriptionTier.FREE, locale),
        get_plan_info(SubscriptionTier.PRO, locale),
        get_plan_info(SubscriptionTier.ENTERPRISE, locale),
    ]

    return request.app.state.templates.TemplateResponse(
        "pricing.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "user": user,
            "current_tier": current_tier.value if current_tier else None,
            "plans": plans,
        },
    )


@router.get("/checkout/{tier}")
def checkout_page(
    tier: str,
    request: Request,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """결제 체크아웃 페이지"""
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)

    try:
        selected_tier = SubscriptionTier(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    # 현재 구독 확인
    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == user.id)
    ).first()
    current_tier = subscription.tier if subscription else SubscriptionTier.FREE

    # 무료 플랜은 체크아웃 불필요
    if selected_tier == SubscriptionTier.FREE:
        return RedirectResponse(url="/subscriptions/pricing", status_code=303)

    # 이미 같은 플랜이면 리다이렉트
    if current_tier == selected_tier:
        return RedirectResponse(url="/dashboard?msg=already_subscribed", status_code=303)

    plan_info = get_plan_info(selected_tier, locale)

    return request.app.state.templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "user": user,
            "plan": plan_info,
            "current_tier": current_tier.value,
        },
    )


@router.post("/checkout/{tier}")
def process_checkout(
    tier: str,
    request: Request,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
    payment_method: str = Form(...),
    card_number: Optional[str] = Form(None),
    expiry: Optional[str] = Form(None),
    cvc: Optional[str] = Form(None),
):
    """결제 처리 (실제 PG 연동 전 모의 처리)"""
    locale = user.locale or "ko"

    try:
        selected_tier = SubscriptionTier(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    # 현재 구독 확인
    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == user.id)
    ).first()
    old_tier = subscription.tier if subscription else SubscriptionTier.FREE

    # 구독 업데이트
    if not subscription:
        subscription = Subscription(
            user_id=user.id,
            tier=selected_tier,
            max_accounts=PLAN_INFO[selected_tier]["max_accounts"],
            active=True,
        )
        session.add(subscription)
    else:
        subscription.tier = selected_tier
        subscription.max_accounts = PLAN_INFO[selected_tier]["max_accounts"]
        subscription.active = True

    # 활동 로그
    session.add(ActivityLog(
        user_id=user.id,
        action=f"subscription_change_{old_tier.value}_to_{selected_tier.value}"
    ))
    session.commit()

    # 이메일 발송
    settings = get_settings()
    if settings.use_resend:
        plan_info = get_plan_info(selected_tier, locale)
        old_plan_info = get_plan_info(old_tier, locale)

        # 결제 확인 이메일
        resend_email_service.send_purchase_confirmation(
            to=user.email,
            name=user.name or user.email,
            plan_name=plan_info["name"],
            amount=plan_info["price"],
            locale=locale,
        )

        # 구독 변경 알림
        change_type = "upgrade" if PLAN_INFO[selected_tier]["price_value"] > PLAN_INFO[old_tier]["price_value"] else "downgrade"
        resend_email_service.send_subscription_change(
            to=user.email,
            name=user.name or user.email,
            old_plan=old_plan_info["name"],
            new_plan=plan_info["name"],
            change_type=change_type,
            locale=locale,
        )

    return RedirectResponse(
        url=f"/subscriptions/success?tier={selected_tier.value}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/success")
def checkout_success(
    request: Request,
    tier: str,
    user: User = Depends(get_current_user),
):
    """결제 성공 페이지"""
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)

    try:
        selected_tier = SubscriptionTier(tier)
    except ValueError:
        selected_tier = SubscriptionTier.FREE

    plan_info = get_plan_info(selected_tier, locale)

    return request.app.state.templates.TemplateResponse(
        "checkout_success.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "user": user,
            "plan": plan_info,
        },
    )


@router.post("/cancel")
def cancel_subscription(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """구독 취소"""
    locale = user.locale or "ko"

    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == user.id)
    ).first()

    if not subscription or subscription.tier == SubscriptionTier.FREE:
        return RedirectResponse(url="/subscriptions/pricing?msg=no_subscription", status_code=303)

    old_tier = subscription.tier
    old_plan_info = get_plan_info(old_tier, locale)

    # 구독 취소 (다음 결제일까지 유지 후 FREE로 전환)
    subscription.cancelled_at = datetime.utcnow()

    session.add(ActivityLog(
        user_id=user.id,
        action=f"subscription_cancel_{old_tier.value}"
    ))
    session.commit()

    # 취소 이메일 발송
    settings = get_settings()
    if settings.use_resend:
        resend_email_service.send_subscription_change(
            to=user.email,
            name=user.name or user.email,
            old_plan=old_plan_info["name"],
            new_plan="",
            change_type="cancel",
            locale=locale,
        )

    return RedirectResponse(url="/subscriptions/pricing?msg=cancelled", status_code=303)


# 레거시 엔드포인트 (호환성 유지)
@router.post("/change")
def change_subscription(
    tier: SubscriptionTier = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """구독 변경 (레거시 API)"""
    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == user.id)
    ).first()
    if not subscription:
        subscription = Subscription(user_id=user.id, tier=tier)
    subscription.tier = tier
    subscription.max_accounts = PLAN_INFO.get(tier, PLAN_INFO[SubscriptionTier.FREE])["max_accounts"]
    session.add(subscription)
    session.commit()
    return {"message": "Subscription updated", "tier": tier.value}
