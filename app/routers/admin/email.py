"""
관리자 이메일 라우터

슈퍼 관리자 이메일 발송 및 관리
"""

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse

from ...config import get_settings
from ...database import get_session
from ...dependencies import require_roles
from ...models import ActivityLog, User, UserRole
from ...services.localization import translator
from ...services.email.super_admin_email import (
    EmailSendError,
    EmailServiceError,
    SuperAdminEmailService,
)

from .helpers import TEST_EMAIL_RECIPIENT

router = APIRouter()


@router.post("/super-admin/email/send")
def send_super_admin_email(
    to_address: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """관리자 이메일 발송"""
    settings = get_settings()
    if not SuperAdminEmailService.is_configured(settings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email service is not configured.",
        )

    if not to_address.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient address is required.",
        )

    if not subject.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject is required.",
        )

    try:
        service = SuperAdminEmailService(settings)
        service.send_email(to_address=to_address, subject=subject, body=body)
    except (EmailSendError, EmailServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    session.add(
        ActivityLog(
            user_id=user.id,
            action="super_admin_email_send",
            details=f"to={to_address} subject={subject[:100]}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?email_sent=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/super-admin/email/send-test")
def send_super_admin_test_email(
    session=Depends(get_session),
    user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
):
    """테스트 이메일 발송"""
    settings = get_settings()
    if not SuperAdminEmailService.is_configured(settings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email service is not configured.",
        )

    strings = translator.load_locale(user.locale)
    super_admin_strings = strings.get("super_admin", {})
    subject = super_admin_strings.get("email_test_subject") or "Creator Control Center test email"
    body_template = super_admin_strings.get("email_test_body") or (
        "Hello,\nThis is an automated test email from the admin console.\nSender: {admin}"
    )
    sender_name = user.name or user.email
    try:
        body = body_template.format(admin=sender_name)
    except Exception:
        body = body_template

    try:
        service = SuperAdminEmailService(settings)
        service.send_email(to_address=TEST_EMAIL_RECIPIENT, subject=subject, body=body)
    except (EmailSendError, EmailServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    session.add(
        ActivityLog(
            user_id=user.id,
            action="super_admin_email_send_test",
            details=f"to={TEST_EMAIL_RECIPIENT} subject={subject[:100]}",
        )
    )
    session.commit()

    return RedirectResponse(
        url="/super-admin?email_test=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )
