"""
문의 관리 라우터

크리에이터 문의 관리 및 처리
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import select

from ...database import get_session
from ...dependencies import require_roles
from ...models import (
    ActivityLog,
    CreatorInquiry,
    InquiryCategory,
    InquiryStatus,
    User,
    UserRole,
)
from ...services.localization import translator

router = APIRouter()


@router.get("/manager/inquiries")
def manager_inquiries(
    request: Request,
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """매니저 문의 관리 페이지"""
    locale = user.locale
    strings = translator.load_locale(locale)

    # 페이지네이션
    page = int(request.query_params.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    # 필터
    status_filter = request.query_params.get("status")
    category_filter = request.query_params.get("category")

    # 쿼리 빌드
    query = select(CreatorInquiry).where(CreatorInquiry.manager_id == user.id)

    if status_filter:
        try:
            query = query.where(CreatorInquiry.status == InquiryStatus(status_filter))
        except ValueError:
            pass

    if category_filter:
        try:
            query = query.where(CreatorInquiry.category == InquiryCategory(category_filter))
        except ValueError:
            pass

    # 전체 수
    from sqlalchemy import func
    total_count = session.exec(
        select(func.count(CreatorInquiry.id))
        .where(CreatorInquiry.manager_id == user.id)
    ).first() or 0

    total_pages = (total_count + per_page - 1) // per_page

    # 문의 목록
    inquiries = session.exec(
        query.order_by(CreatorInquiry.created_at.desc())
        .limit(per_page)
        .offset(offset)
    ).all()

    # 크리에이터 정보
    creator_ids = [inq.creator_id for inq in inquiries]
    creators = session.exec(
        select(User).where(User.id.in_(creator_ids))
    ).all() if creator_ids else []
    creator_lookup = {c.id: c for c in creators}

    return request.app.state.templates.TemplateResponse(
        "admin/manager_inquiries.html",
        {
            "request": request,
            "user": user,
            "locale": locale,
            "t": strings,
            "inquiries": inquiries,
            "creator_lookup": creator_lookup,
            "statuses": list(InquiryStatus),
            "categories": list(InquiryCategory),
            "current_status": status_filter,
            "current_category": category_filter,
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": total_pages,
        },
    )


@router.post("/manager/inquiry/{inquiry_id}/respond")
def respond_inquiry(
    inquiry_id: int,
    response_text: str = Form(...),
    new_status: InquiryStatus = Form(InquiryStatus.IN_PROGRESS),
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """문의에 답변"""
    inquiry = session.get(CreatorInquiry, inquiry_id)
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found"
        )

    if inquiry.manager_id != user.id and user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    inquiry.response = response_text.strip()
    inquiry.status = new_status
    inquiry.responded_at = datetime.utcnow()
    session.add(inquiry)

    session.add(
        ActivityLog(
            user_id=user.id,
            action="inquiry_respond",
            details=f"inquiry_id={inquiry_id}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/manager/inquiries",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/manager/inquiry/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: int,
    new_status: InquiryStatus = Form(...),
    user: User = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    session=Depends(get_session),
):
    """문의 상태 변경"""
    inquiry = session.get(CreatorInquiry, inquiry_id)
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found"
        )

    if inquiry.manager_id != user.id and user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    inquiry.status = new_status
    session.add(inquiry)

    session.add(
        ActivityLog(
            user_id=user.id,
            action="inquiry_status_update",
            details=f"inquiry_id={inquiry_id} status={new_status.value}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/manager/inquiries",
        status_code=status.HTTP_303_SEE_OTHER,
    )
