"""
결제 관리 라우터

결제 생성 및 상태 관리
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from ...database import get_session
from ...dependencies import require_roles
from ...models import (
    ActivityLog,
    Payment,
    PaymentStatus,
    User,
    UserRole,
)

router = APIRouter()


def _parse_datetime(value: str | None) -> datetime | None:
    """ISO 형식 문자열에서 datetime 파싱"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {value}") from e


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
    """결제 내역 생성"""
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        period_start = _parse_datetime(billing_period_start)
        period_end = _parse_datetime(billing_period_end)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    currency_value = (currency or "KRW").strip().upper()[:3] or "KRW"
    payment = Payment(
        user_id=user_id,
        amount=max(amount, 0),
        currency=currency_value,
        status=status_value,
        description=description.strip() if description else None,
        billing_period_start=period_start,
        billing_period_end=period_end,
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
    """결제 상태 변경"""
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

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
