from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ..config import get_settings
from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import (
    ActivityLog,
    ChannelAccount,
    CreatorInquiry,
    InquiryCategory,
    InquiryStatus,
    ManagerAPIKey,
    ManagerCreatorLink,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionTier,
    User,
    UserRole,
)
from ..services.localization import translator

router = APIRouter()


@router.get("/super-admin")
def super_admin_dashboard(
    request: Request,
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    locale = user.locale
    strings = translator.load_locale(locale)
    users = session.exec(select(User).order_by(User.created_at.desc())).all()
    subscriptions = session.exec(select(Subscription)).all()

    # 회원 구분: 기업(MANAGER) / 개인(CREATOR)
    business_users = [u for u in users if u.role == UserRole.MANAGER or u.role == UserRole.ADMIN]
    personal_users = [u for u in users if u.role == UserRole.CREATOR]

    # 최근 결제 내역 (100개)
    recent_payments = session.exec(
        select(Payment).order_by(Payment.created_at.desc()).limit(100)
    ).all()

    # 결제 통계
    from sqlalchemy import func
    total_revenue = session.exec(
        select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.PAID)
    ).first() or 0

    user_lookup = {u.id: u for u in users}

    # AI API 키 확인 (슈퍼관리자 전용)
    settings = get_settings()
    gemini_api_key_set = hasattr(settings, 'gemini_api_key') and settings.gemini_api_key and settings.gemini_api_key != ""

    # AI PD 시스템 프롬프트 가져오기
    from ..services.ai_pd_service import AIPDService
    ai_system_prompt = AIPDService.get_system_prompt()

    response = request.app.state.templates.TemplateResponse(
        "super_admin.html",
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
            "logs": [],  # 빈 로그 (템플릿 호환성을 위해)
            "roles": list(UserRole),
            "tiers": list(SubscriptionTier),
            "payment_statuses": list(PaymentStatus),
            "user_lookup": user_lookup,
            "gemini_api_key_set": gemini_api_key_set,
            "ai_system_prompt": ai_system_prompt,
        },
    )

    return response


@router.post("/super-admin/promote")
def promote_user(
    request: Request,
    email: str = Form(...),
    role: UserRole = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    target = session.exec(select(User).where(User.email == email)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.role = role
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="role_update",
            details=f"{target.email}:{role.value}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/status")
def update_user_status(
    request: Request,
    user_id: int = Form(...),
    is_active: bool = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_active = is_active
    session.add(target)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="user_status",
            details=f"{target.email}:{'active' if is_active else 'inactive'}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/subscription")
def update_subscription(
    request: Request,
    user_id: int = Form(...),
    tier: SubscriptionTier = Form(...),
    max_accounts: int = Form(1),
    active: bool = Form(False),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    subscription = session.exec(select(Subscription).where(Subscription.user_id == user_id)).first()
    if not subscription:
        subscription = Subscription(user_id=user_id)
    subscription.tier = tier
    subscription.max_accounts = max(1, max_accounts)
    subscription.active = active
    session.add(subscription)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="subscription_update",
            details=f"{target.email}:{tier.value}:{'active' if active else 'inactive'}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@router.post("/super-admin/payment/create")
def create_payment(
    request: Request,
    user_id: int = Form(...),
    amount: float = Form(...),
    currency: str = Form("KRW"),
    status_value: PaymentStatus = Form(PaymentStatus.PENDING),
    description: str | None = Form(None),
    billing_period_start: str | None = Form(None),
    billing_period_end: str | None = Form(None),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    currency_value = (currency or "KRW").strip().upper()[:3] or "KRW"
    payment = Payment(
        user_id=user_id,
        amount=max(amount, 0),
        currency=currency_value,
        status=status_value,
        description=description.strip() if description else None,
        billing_period_start=_parse_datetime(billing_period_start),
        billing_period_end=_parse_datetime(billing_period_end),
    )
    session.add(payment)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="payment_create",
            details=f"{target.email}:{payment.amount}{payment.currency}:{payment.status.value}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/super-admin/payment/status")
def update_payment_status(
    request: Request,
    payment_id: int = Form(...),
    status_value: PaymentStatus = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = status_value
    session.add(payment)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="payment_status",
            details=f"{payment.id}:{payment.status.value}",
        )
    )
    session.commit()
    return RedirectResponse(url="/super-admin", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/manager/dashboard")
def manager_dashboard(
    request: Request,
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """기업 관리자 전용 대시보드"""
    from sqlalchemy.orm import selectinload
    from ..models import ChannelAccount
    from ..services.social_fetcher import fetch_channel_snapshots

    locale = user.locale
    strings = translator.load_locale(locale)

    # 매니저와 연결된 모든 링크 조회
    all_links = session.exec(
        select(ManagerCreatorLink).where(ManagerCreatorLink.manager_id == user.id)
    ).all()

    # 승인된 링크와 대기 중인 링크 분리
    approved_creators = [link for link in all_links if link.approved]
    pending_approvals = [link for link in all_links if not link.approved]

    # 크리에이터 정보 조회
    creator_ids = [link.creator_id for link in all_links]
    creators = session.exec(select(User).where(User.id.in_(creator_ids))).all() if creator_ids else []
    creator_lookup = {c.id: c for c in creators}

    # 크리에이터별 구독 정보
    subscriptions = session.exec(select(Subscription).where(Subscription.user_id.in_(creator_ids))).all() if creator_ids else []
    creator_subscriptions = {s.user_id: s for s in subscriptions}

    # 승인된 크리에이터의 채널 정보
    approved_creator_ids = [link.creator_id for link in approved_creators]
    creator_channels_list = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id.in_(approved_creator_ids))
        .options(selectinload(ChannelAccount.credential))
    ).all() if approved_creator_ids else []

    # 크리에이터별로 채널 그룹화
    creator_channels = {}
    for channel in creator_channels_list:
        if channel.owner_id not in creator_channels:
            creator_channels[channel.owner_id] = []
        creator_channels[channel.owner_id].append(channel)

    # 채널 수 카운트
    creator_channel_counts = {creator_id: len(channels) for creator_id, channels in creator_channels.items()}
    total_channels = sum(creator_channel_counts.values())

    # 모든 채널의 스냅샷 가져오기
    creator_snapshots = fetch_channel_snapshots(creator_channels_list)

    # API 키 존재 여부 확인
    api_key_record = session.exec(select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)).first()
    has_api_key = api_key_record is not None

    return request.app.state.templates.TemplateResponse(
        "manager_dashboard.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "approved_creators": approved_creators,
            "pending_approvals": pending_approvals,
            "creator_lookup": creator_lookup,
            "creator_subscriptions": creator_subscriptions,
            "creator_channels": creator_channels,
            "creator_channel_counts": creator_channel_counts,
            "total_channels": total_channels,
            "creator_snapshots": creator_snapshots,
            "has_api_key": has_api_key,
        },
    )


@router.post("/manager/approve")
def approve_manager(
    request: Request,
    creator_email: str = Form(...),
    manager_email: str = Form(...),
    approve: bool = Form(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    creator = session.exec(select(User).where(User.email == creator_email)).first()
    manager = session.exec(select(User).where(User.email == manager_email)).first()
    if not creator or not manager:
        raise HTTPException(status_code=404, detail="User not found")

    link = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.creator_id == creator.id)
        .where(ManagerCreatorLink.manager_id == manager.id)
    ).first()

    if approve:
        if not link:
            link = ManagerCreatorLink(
                creator_id=creator.id,
                manager_id=manager.id,
                approved=True,
                connected_at=datetime.utcnow(),
            )
        else:
            link.approved = True
            link.connected_at = datetime.utcnow()
        session.add(link)
        session.commit()
    else:
        if link:
            session.delete(link)
            session.commit()

    return RedirectResponse(url="/manager/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/manager/invite")
def create_manager_invite(
    request: Request,
    creator_email: str = Form(...),
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """크리에이터 초대 링크 생성"""
    # 크리에이터가 이미 존재하는지 확인
    creator = session.exec(select(User).where(User.email == creator_email)).first()

    # 초대 링크 생성 (실제로는 토큰 기반으로 구현해야 함)
    invite_link = f"{request.base_url}signup?invited_by={user.id}&role=creator"

    # 세션에 초대 링크 저장 (임시)
    return RedirectResponse(
        url=f"/manager/dashboard?invite_link={invite_link}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/manager/creator/{creator_id}")
def view_creator_detail(
    creator_id: int,
    request: Request,
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """특정 크리에이터의 상세 정보 조회"""
    from sqlalchemy.orm import selectinload
    from ..models import ChannelAccount
    from ..services.social_fetcher import fetch_channel_snapshots

    # 매니저와 크리에이터의 연결 확인
    link = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.manager_id == user.id)
        .where(ManagerCreatorLink.creator_id == creator_id)
        .where(ManagerCreatorLink.approved == True)  # noqa: E712
    ).first()

    if not link:
        raise HTTPException(status_code=403, detail="이 크리에이터의 정보에 접근할 수 없습니다.")

    creator = session.get(User, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")

    # 크리에이터의 채널 및 스냅샷 조회
    channels = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == creator_id)
        .options(selectinload(ChannelAccount.credential))
    ).all()

    snapshots = fetch_channel_snapshots(channels)

    subscription = session.exec(select(Subscription).where(Subscription.user_id == creator_id)).first()

    locale = user.locale
    strings = translator.load_locale(locale)

    return request.app.state.templates.TemplateResponse(
        "creator_detail.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "creator": creator,
            "channels": channels,
            "snapshots": snapshots,
            "subscription": subscription,
        },
    )


@router.get("/manager/export/pdf")
def export_manager_dashboard_pdf(
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """기업 관리자용 통합 PDF 리포트 다운로드"""
    from fastapi.responses import StreamingResponse
    from sqlalchemy.orm import selectinload
    from ..models import ChannelAccount
    from ..services.social_fetcher import fetch_channel_snapshots
    from ..services.pdf_generator import generate_manager_pdf

    # 승인된 크리에이터 정보 조회
    approved_links = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.manager_id == user.id)
        .where(ManagerCreatorLink.approved == True)  # noqa: E712
    ).all()

    creator_ids = [link.creator_id for link in approved_links]
    creators = session.exec(select(User).where(User.id.in_(creator_ids))).all() if creator_ids else []

    # 크리에이터별 채널 정보
    creator_channels_list = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id.in_(creator_ids))
        .options(selectinload(ChannelAccount.credential))
    ).all() if creator_ids else []

    creator_channels = {}
    for channel in creator_channels_list:
        if channel.owner_id not in creator_channels:
            creator_channels[channel.owner_id] = []
        creator_channels[channel.owner_id].append(channel)

    # 스냅샷 조회
    creator_snapshots = fetch_channel_snapshots(creator_channels_list)

    # PDF 생성
    pdf_buffer = generate_manager_pdf(user, creators, creator_channels, creator_snapshots)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"manager_report_{timestamp}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/manager/creator/{creator_id}/export/csv")
def export_creator_csv(
    creator_id: int,
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """특정 크리에이터의 데이터를 CSV로 내보내기"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    from sqlalchemy.orm import selectinload
    from ..models import ChannelAccount
    from ..services.social_fetcher import fetch_channel_snapshots

    # 권한 확인
    link = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.manager_id == user.id)
        .where(ManagerCreatorLink.creator_id == creator_id)
        .where(ManagerCreatorLink.approved == True)  # noqa: E712
    ).first()

    if not link:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    creator = session.get(User, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")

    channels = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == creator_id)
        .options(selectinload(ChannelAccount.credential))
    ).all()
    snapshots = fetch_channel_snapshots(channels)

    # CSV 생성
    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow([
        "크리에이터 이메일",
        "크리에이터 이름",
        "플랫폼",
        "계정명",
        "팔로워",
        "성장률(%)",
        "참여율(%)",
        "최근 게시일"
    ])

    # 데이터
    for channel in channels:
        snapshot = snapshots.get(channel.id, {})
        writer.writerow([
            creator.email,
            creator.name or "-",
            channel.platform,
            channel.account_name,
            snapshot.get("followers", 0),
            snapshot.get("growth_rate", 0),
            snapshot.get("engagement_rate", 0),
            snapshot.get("last_post_date", "")[:10] if snapshot.get("last_post_date") else "-"
        ])

    output.seek(0)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"creator_{creator_id}_report_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/manager/creator/{creator_id}/export/pdf")
def export_creator_pdf(
    creator_id: int,
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """특정 크리에이터의 데이터를 PDF로 내보내기"""
    from fastapi.responses import StreamingResponse
    from sqlalchemy.orm import selectinload
    from ..models import ChannelAccount
    from ..services.social_fetcher import fetch_channel_snapshots
    from ..services.pdf_generator import generate_dashboard_pdf

    # 권한 확인
    link = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.manager_id == user.id)
        .where(ManagerCreatorLink.creator_id == creator_id)
        .where(ManagerCreatorLink.approved == True)  # noqa: E712
    ).first()

    if not link:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    creator = session.get(User, creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")

    channels = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == creator_id)
        .options(selectinload(ChannelAccount.credential))
    ).all()
    snapshots = fetch_channel_snapshots(channels)

    # PDF 생성 (대시보드용 함수 재사용)
    pdf_buffer = generate_dashboard_pdf(creator, channels, snapshots)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"creator_{creator_id}_report_{timestamp}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== Gemini API 키 관리 ====================

@router.post("/manager/api-key/save")
def save_gemini_api_key(
    request: Request,
    api_key: str = Form(...),
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """Gemini API 키 저장 (암호화)"""
    # 기존 키가 있는지 확인
    existing_key = session.exec(
        select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)
    ).first()

    if existing_key:
        # 업데이트
        existing_key.api_key = api_key  # setter를 통해 자동 암호화
        session.add(existing_key)
    else:
        # 새로 생성
        new_key = ManagerAPIKey(manager_id=user.id)
        new_key.api_key = api_key  # setter를 통해 자동 암호화
        session.add(new_key)

    session.add(
        ActivityLog(
            user_id=user.id,
            action="api_key_saved",
            details="Gemini API 키 저장됨"
        )
    )
    session.commit()

    return RedirectResponse(url="/manager/dashboard?api_key_saved=true", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/manager/api-key/delete")
def delete_gemini_api_key(
    request: Request,
    user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    session=Depends(get_session),
):
    """Gemini API 키 삭제"""
    api_key_record = session.exec(
        select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)
    ).first()

    if api_key_record:
        session.delete(api_key_record)
        session.add(
            ActivityLog(
                user_id=user.id,
                action="api_key_deleted",
                details="Gemini API 키 삭제됨"
            )
        )
        session.commit()

    return RedirectResponse(url="/manager/dashboard?api_key_deleted=true", status_code=status.HTTP_303_SEE_OTHER)


# ==================== 크리에이터 문의 관리 ====================

@router.post("/manager/inquiry/create")
def create_inquiry(
    request: Request,
    creator_id: int = Form(...),
    category: InquiryCategory = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    session=Depends(get_session),
):
    """크리에이터 문의 수동 생성 (관리자가 대신 기록)"""
    # 관리자-크리에이터 연결 확인
    link = session.exec(
        select(ManagerCreatorLink)
        .where(ManagerCreatorLink.manager_id == user.id)
        .where(ManagerCreatorLink.creator_id == creator_id)
        .where(ManagerCreatorLink.approved == True)  # noqa: E712
    ).first()

    if not link:
        raise HTTPException(status_code=403, detail="이 크리에이터를 관리할 권한이 없습니다.")

    # 문의 생성
    inquiry = CreatorInquiry(
        creator_id=creator_id,
        manager_id=user.id,
        category=category,
        subject=subject,
        message=message,
        status=InquiryStatus.PENDING
    )
    session.add(inquiry)
    session.commit()

    return RedirectResponse(
        url=f"/manager/inquiries?created=true",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/manager/inquiries")
def view_inquiries(
    request: Request,
    user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    session=Depends(get_session),
):
    """모든 문의 조회"""
    from sqlalchemy.orm import selectinload

    # 이 관리자가 관리하는 크리에이터들의 문의만 조회
    inquiries = session.exec(
        select(CreatorInquiry)
        .where(CreatorInquiry.manager_id == user.id)
        .order_by(CreatorInquiry.created_at.desc())
    ).all()

    # 크리에이터 정보 조회
    creator_ids = list(set([inq.creator_id for inq in inquiries]))
    creators = session.exec(select(User).where(User.id.in_(creator_ids))).all() if creator_ids else []
    creator_lookup = {c.id: c for c in creators}

    # API 키 존재 여부 확인
    api_key_record = session.exec(
        select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)
    ).first()
    has_api_key = api_key_record is not None

    locale = user.locale
    strings = translator.load_locale(locale)

    return request.app.state.templates.TemplateResponse(
        "manager_inquiries.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "inquiries": inquiries,
            "creator_lookup": creator_lookup,
            "has_api_key": has_api_key,
            "inquiry_statuses": list(InquiryStatus),
            "inquiry_categories": list(InquiryCategory),
        },
    )


@router.post("/manager/inquiry/{inquiry_id}/generate-ai-response")
def generate_ai_response(
    inquiry_id: int,
    request: Request,
    user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    session=Depends(get_session),
):
    """AI를 사용하여 답변 초안 생성"""
    from sqlalchemy.orm import selectinload

    # 문의 조회
    inquiry = session.get(CreatorInquiry, inquiry_id)
    if not inquiry or inquiry.manager_id != user.id:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")

    # API 키 조회
    api_key_record = session.exec(
        select(ManagerAPIKey).where(ManagerAPIKey.manager_id == user.id)
    ).first()

    if not api_key_record:
        raise HTTPException(
            status_code=400,
            detail="Gemini API 키가 설정되지 않았습니다. 먼저 API 키를 등록해주세요."
        )

    # 크리에이터 정보 조회
    creator = session.get(User, inquiry.creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")

    # 크리에이터의 채널 정보 조회 (컨텍스트용)
    channels = session.exec(
        select(ChannelAccount)
        .where(ChannelAccount.owner_id == creator.id)
    ).all()

    subscription = session.exec(
        select(Subscription).where(Subscription.user_id == creator.id)
    ).first()

    # 컨텍스트 데이터 준비
    context_data = {
        "subscription": subscription.tier.value if subscription else "free",
        "channel_count": len(channels),
        "channels": [
            {
                "platform": ch.platform,
                "account_name": ch.account_name,
                "followers": ch.followers
            }
            for ch in channels
        ]
    }

    # AI 서비스 사용
    try:
        from ..services.gemini_ai import get_gemini_service

        gemini = get_gemini_service(api_key_record.api_key)

        ai_response = gemini.generate_cs_response(
            inquiry_subject=inquiry.subject,
            inquiry_message=inquiry.message,
            inquiry_category=inquiry.category.value,
            creator_info={
                "name": creator.name,
                "email": creator.email,
                "organization": creator.organization
            },
            context_data=context_data
        )

        # 문의 업데이트
        inquiry.ai_draft_response = ai_response
        inquiry.status = InquiryStatus.AI_DRAFT_READY
        inquiry.updated_at = datetime.utcnow()
        session.add(inquiry)
        session.commit()

        return RedirectResponse(
            url=f"/manager/inquiries?ai_generated={inquiry_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 답변 생성 실패: {str(e)}")


@router.post("/manager/inquiry/{inquiry_id}/send-response")
def send_inquiry_response(
    inquiry_id: int,
    request: Request,
    final_response: str = Form(...),
    user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    session=Depends(get_session),
):
    """최종 답변 전송 (실제로는 저장만, 이메일 발송은 추후 구현 가능)"""
    inquiry = session.get(CreatorInquiry, inquiry_id)
    if not inquiry or inquiry.manager_id != user.id:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")

    inquiry.final_response = final_response
    inquiry.status = InquiryStatus.ANSWERED
    inquiry.responded_at = datetime.utcnow()
    inquiry.updated_at = datetime.utcnow()

    session.add(inquiry)
    session.add(
        ActivityLog(
            user_id=user.id,
            action="inquiry_answered",
            details=f"문의 #{inquiry_id} 답변 완료"
        )
    )
    session.commit()

    return RedirectResponse(
        url=f"/manager/inquiries?answered={inquiry_id}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/manager/inquiry/{inquiry_id}/update-status")
def update_inquiry_status(
    inquiry_id: int,
    request: Request,
    new_status: InquiryStatus = Form(...),
    user: User = Depends(require_roles([UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    session=Depends(get_session),
):
    """문의 상태 업데이트"""
    inquiry = session.get(CreatorInquiry, inquiry_id)
    if not inquiry or inquiry.manager_id != user.id:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")

    inquiry.status = new_status
    inquiry.updated_at = datetime.utcnow()

    session.add(inquiry)
    session.commit()

    return RedirectResponse(
        url="/manager/inquiries",
        status_code=status.HTTP_303_SEE_OTHER
    )
