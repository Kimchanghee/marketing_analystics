"""Resend email service for transactional emails.

This service handles all email communications including:
- Email verification codes
- Password reset links
- Welcome emails
- Purchase confirmations
- Admin notifications
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx

from ...config import get_settings

logger = logging.getLogger(__name__)


class EmailType(Enum):
    """Types of transactional emails."""

    VERIFICATION_CODE = "verification_code"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    SIGNUP_COMPLETE = "signup_complete"
    PURCHASE_COMPLETE = "purchase_complete"
    ADMIN_NOTIFICATION = "admin_notification"
    SUBSCRIPTION_CHANGE = "subscription_change"


@dataclass
class EmailResult:
    """Result of an email send operation."""

    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class ResendEmailService:
    """Service for sending emails via Resend API."""

    API_URL = "https://api.resend.com/emails"

    def __init__(self):
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        """Check if Resend is properly configured."""
        return bool(self.settings.resend_api_key)

    def _get_headers(self) -> dict:
        """Get API headers."""
        return {
            "Authorization": f"Bearer {self.settings.resend_api_key}",
            "Content-Type": "application/json",
        }

    def _get_from_address(self) -> str:
        """Get formatted from address."""
        return f"{self.settings.resend_from_name} <{self.settings.resend_from_email}>"

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        """Send an email via Resend API.

        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML content
            text: Plain text content (optional)
            reply_to: Reply-to address (optional)

        Returns:
            EmailResult with success status and message ID or error
        """
        if not self.is_configured:
            logger.warning("Resend API key not configured, skipping email send")
            return EmailResult(success=False, error="Resend not configured")

        payload = {
            "from": self._get_from_address(),
            "to": [to],
            "subject": subject,
            "html": html,
        }

        if text:
            payload["text"] = text
        if reply_to:
            payload["reply_to"] = reply_to

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Email sent successfully to {to}, ID: {data.get('id')}")
                    return EmailResult(success=True, message_id=data.get("id"))
                else:
                    error_msg = response.text
                    logger.error(f"Failed to send email to {to}: {error_msg}")
                    return EmailResult(success=False, error=error_msg)

        except Exception as e:
            logger.exception(f"Exception sending email to {to}: {e}")
            return EmailResult(success=False, error=str(e))

    def send_email_sync(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> EmailResult:
        """Synchronous version of send_email for non-async contexts."""
        if not self.is_configured:
            logger.warning("Resend API key not configured, skipping email send")
            return EmailResult(success=False, error="Resend not configured")

        payload = {
            "from": self._get_from_address(),
            "to": [to],
            "subject": subject,
            "html": html,
        }

        if text:
            payload["text"] = text
        if reply_to:
            payload["reply_to"] = reply_to

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.API_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Email sent successfully to {to}, ID: {data.get('id')}")
                    return EmailResult(success=True, message_id=data.get("id"))
                else:
                    error_msg = response.text
                    logger.error(f"Failed to send email to {to}: {error_msg}")
                    return EmailResult(success=False, error=error_msg)

        except Exception as e:
            logger.exception(f"Exception sending email to {to}: {e}")
            return EmailResult(success=False, error=str(e))

    # ===== Email Templates =====

    def send_verification_code(self, to: str, code: str, locale: str = "ko") -> EmailResult:
        """Send email verification code."""
        if locale == "ko":
            subject = "[Creator Control Center] 이메일 인증 코드"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">이메일 인증</h2>
                <p>안녕하세요,</p>
                <p>아래 인증 코드를 입력하여 이메일을 인증해주세요.</p>
                <div style="background: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #333;">{code}</span>
                </div>
                <p style="color: #666; font-size: 14px;">이 코드는 15분 동안 유효합니다.</p>
                <p style="color: #666; font-size: 14px;">본인이 요청하지 않은 경우 이 이메일을 무시해주세요.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """
        else:
            subject = "[Creator Control Center] Email Verification Code"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">Email Verification</h2>
                <p>Hello,</p>
                <p>Please enter the following code to verify your email address.</p>
                <div style="background: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #333;">{code}</span>
                </div>
                <p style="color: #666; font-size: 14px;">This code is valid for 15 minutes.</p>
                <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """

        return self.send_email_sync(to, subject, html)

    def send_password_reset(self, to: str, reset_link: str, locale: str = "ko") -> EmailResult:
        """Send password reset email."""
        if locale == "ko":
            subject = "[Creator Control Center] 비밀번호 재설정"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">비밀번호 재설정</h2>
                <p>안녕하세요,</p>
                <p>비밀번호 재설정을 요청하셨습니다. 아래 버튼을 클릭하여 새 비밀번호를 설정하세요.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">비밀번호 재설정</a>
                </div>
                <p style="color: #666; font-size: 14px;">이 링크는 30분 동안 유효합니다.</p>
                <p style="color: #666; font-size: 14px;">본인이 요청하지 않은 경우 이 이메일을 무시해주세요.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """
        else:
            subject = "[Creator Control Center] Password Reset"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">Password Reset</h2>
                <p>Hello,</p>
                <p>You requested a password reset. Click the button below to set a new password.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
                </div>
                <p style="color: #666; font-size: 14px;">This link is valid for 30 minutes.</p>
                <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """

        return self.send_email_sync(to, subject, html)

    def send_welcome_email(self, to: str, name: str, locale: str = "ko") -> EmailResult:
        """Send welcome email after signup."""
        if locale == "ko":
            subject = "[Creator Control Center] 가입을 환영합니다!"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">환영합니다, {name}님! 🎉</h2>
                <p>Creator Control Center에 가입해 주셔서 감사합니다.</p>
                <p>이제 다음과 같은 기능을 이용하실 수 있습니다:</p>
                <ul style="color: #555; line-height: 1.8;">
                    <li>SNS 채널 통합 관리</li>
                    <li>실시간 통계 분석</li>
                    <li>AI PD 비서 기능</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">대시보드로 이동</a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """
        else:
            subject = "[Creator Control Center] Welcome!"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">Welcome, {name}! 🎉</h2>
                <p>Thank you for joining Creator Control Center.</p>
                <p>You now have access to:</p>
                <ul style="color: #555; line-height: 1.8;">
                    <li>Unified SNS channel management</li>
                    <li>Real-time analytics</li>
                    <li>AI PD assistant</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">Go to Dashboard</a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """

        return self.send_email_sync(to, subject, html)

    def send_purchase_confirmation(
        self,
        to: str,
        name: str,
        plan_name: str,
        amount: str,
        locale: str = "ko",
    ) -> EmailResult:
        """Send purchase confirmation email."""
        if locale == "ko":
            subject = "[Creator Control Center] 구매 완료"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">구매가 완료되었습니다! ✅</h2>
                <p>{name}님, 감사합니다.</p>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>플랜:</strong> {plan_name}</p>
                    <p style="margin: 5px 0;"><strong>결제 금액:</strong> {amount}</p>
                </div>
                <p>구독이 즉시 활성화되었습니다. 새로운 기능을 마음껏 사용해보세요!</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">대시보드로 이동</a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """
        else:
            subject = "[Creator Control Center] Purchase Confirmed"
            html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">Purchase Complete! ✅</h2>
                <p>Thank you, {name}.</p>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Plan:</strong> {plan_name}</p>
                    <p style="margin: 5px 0;"><strong>Amount:</strong> {amount}</p>
                </div>
                <p>Your subscription is now active. Enjoy the new features!</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">Go to Dashboard</a>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">Creator Control Center</p>
            </div>
            """

        return self.send_email_sync(to, subject, html)

    def send_admin_notification(
        self,
        to: str,
        subject_text: str,
        message: str,
    ) -> EmailResult:
        """Send admin notification email."""
        subject = f"[Creator Control Center Admin] {subject_text}"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Admin Notification</h2>
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;">{message}</p>
            </div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Creator Control Center - Admin Panel</p>
        </div>
        """

        return self.send_email_sync(to, subject, html)

    def send_subscription_change(
        self,
        to: str,
        name: str,
        old_plan: str,
        new_plan: str,
        change_type: str,
        locale: str = "ko",
    ) -> EmailResult:
        """Send subscription change notification."""
        templates = {
            "ko": {
                "upgrade": {
                    "subject": "[Creator Control Center] 구독 플랜이 업그레이드되었습니다",
                    "title": "구독 업그레이드 완료 🎉",
                    "message": f"{name}님, 구독 플랜이 업그레이드되었습니다.",
                    "detail": f"<strong>{old_plan}</strong> → <strong>{new_plan}</strong>",
                    "note": "새로운 기능을 마음껏 사용해보세요!",
                },
                "downgrade": {
                    "subject": "[Creator Control Center] 구독 플랜이 변경되었습니다",
                    "title": "구독 플랜 변경 안내",
                    "message": f"{name}님, 구독 플랜이 변경되었습니다.",
                    "detail": f"<strong>{old_plan}</strong> → <strong>{new_plan}</strong>",
                    "note": "다음 결제일부터 새 플랜이 적용됩니다.",
                },
                "cancel": {
                    "subject": "[Creator Control Center] 구독이 취소되었습니다",
                    "title": "구독 취소 안내",
                    "message": f"{name}님, 구독이 취소 요청되었습니다.",
                    "detail": f"현재 플랜: <strong>{old_plan}</strong>",
                    "note": "구독 기간 종료 시까지 서비스를 이용하실 수 있습니다.",
                },
            },
            "en": {
                "upgrade": {
                    "subject": "[Creator Control Center] Your subscription has been upgraded",
                    "title": "Subscription Upgraded 🎉",
                    "message": f"Hello {name}, your subscription has been upgraded.",
                    "detail": f"<strong>{old_plan}</strong> → <strong>{new_plan}</strong>",
                    "note": "Enjoy your new features!",
                },
                "downgrade": {
                    "subject": "[Creator Control Center] Your subscription has been changed",
                    "title": "Subscription Changed",
                    "message": f"Hello {name}, your subscription has been changed.",
                    "detail": f"<strong>{old_plan}</strong> → <strong>{new_plan}</strong>",
                    "note": "The new plan will take effect from your next billing date.",
                },
                "cancel": {
                    "subject": "[Creator Control Center] Your subscription has been cancelled",
                    "title": "Subscription Cancelled",
                    "message": f"Hello {name}, your subscription cancellation has been requested.",
                    "detail": f"Current plan: <strong>{old_plan}</strong>",
                    "note": "You can continue using the service until the end of your billing period.",
                },
            },
            "ja": {
                "upgrade": {
                    "subject": "[Creator Control Center] サブスクリプションがアップグレードされました",
                    "title": "サブスクリプションアップグレード完了 🎉",
                    "message": f"{name}様、サブスクリプションがアップグレードされました。",
                    "detail": f"<strong>{old_plan}</strong> → <strong>{new_plan}</strong>",
                    "note": "新機能をお楽しみください！",
                },
                "downgrade": {
                    "subject": "[Creator Control Center] サブスクリプションが変更されました",
                    "title": "サブスクリプション変更のお知らせ",
                    "message": f"{name}様、サブスクリプションが変更されました。",
                    "detail": f"<strong>{old_plan}</strong> → <strong>{new_plan}</strong>",
                    "note": "次回請求日から新プランが適用されます。",
                },
                "cancel": {
                    "subject": "[Creator Control Center] サブスクリプションがキャンセルされました",
                    "title": "サブスクリプションキャンセルのお知らせ",
                    "message": f"{name}様、サブスクリプションのキャンセルが受け付けられました。",
                    "detail": f"現在のプラン: <strong>{old_plan}</strong>",
                    "note": "請求期間終了まではサービスをご利用いただけます。",
                },
            },
        }

        lang_templates = templates.get(locale, templates["en"])
        template = lang_templates.get(change_type, lang_templates["upgrade"])

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">{template['title']}</h2>
            <p>{template['message']}</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <p style="margin: 0; font-size: 18px;">{template['detail']}</p>
            </div>
            <p style="color: #666;">{template['note']}</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">대시보드로 이동</a>
            </div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Creator Control Center</p>
        </div>
        """

        return self.send_email_sync(to, template["subject"], html)

    def send_event_notification(
        self,
        to: str,
        name: str,
        event_title: str,
        event_description: str,
        event_date: Optional[str] = None,
        cta_link: Optional[str] = None,
        cta_text: Optional[str] = None,
        locale: str = "ko",
    ) -> EmailResult:
        """Send event/promotion notification."""
        labels = {
            "ko": {"subject_prefix": "이벤트", "cta_default": "자세히 보기", "date_label": "일시"},
            "en": {"subject_prefix": "Event", "cta_default": "Learn More", "date_label": "Date"},
            "ja": {"subject_prefix": "イベント", "cta_default": "詳しく見る", "date_label": "日時"},
        }
        label = labels.get(locale, labels["en"])

        subject = f"[Creator Control Center] {label['subject_prefix']}: {event_title}"

        date_html = f"<p><strong>{label['date_label']}:</strong> {event_date}</p>" if event_date else ""
        cta_html = ""
        if cta_link:
            cta_label = cta_text or label["cta_default"]
            cta_html = f"""
            <div style="text-align: center; margin: 30px 0;">
                <a href="{cta_link}" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">{cta_label}</a>
            </div>
            """

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">🎉 {event_title}</h2>
            <p>안녕하세요 {name}님,</p>
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; margin: 20px 0;">
                <p style="margin: 0; font-size: 16px; line-height: 1.6;">{event_description}</p>
            </div>
            {date_html}
            {cta_html}
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Creator Control Center</p>
        </div>
        """

        return self.send_email_sync(to, subject, html)

    def send_announcement(
        self,
        to: str,
        name: str,
        announcement_title: str,
        announcement_content: str,
        announcement_type: str = "info",
        locale: str = "ko",
    ) -> EmailResult:
        """Send announcement/notice email.

        Args:
            announcement_type: 'info', 'warning', 'update', 'maintenance'
        """
        labels = {
            "ko": {
                "info": {"prefix": "공지", "icon": "📢"},
                "warning": {"prefix": "중요 공지", "icon": "⚠️"},
                "update": {"prefix": "업데이트", "icon": "🆕"},
                "maintenance": {"prefix": "점검 안내", "icon": "🔧"},
            },
            "en": {
                "info": {"prefix": "Notice", "icon": "📢"},
                "warning": {"prefix": "Important", "icon": "⚠️"},
                "update": {"prefix": "Update", "icon": "🆕"},
                "maintenance": {"prefix": "Maintenance", "icon": "🔧"},
            },
            "ja": {
                "info": {"prefix": "お知らせ", "icon": "📢"},
                "warning": {"prefix": "重要なお知らせ", "icon": "⚠️"},
                "update": {"prefix": "アップデート", "icon": "🆕"},
                "maintenance": {"prefix": "メンテナンス", "icon": "🔧"},
            },
        }

        type_colors = {
            "info": "#4F46E5",
            "warning": "#DC2626",
            "update": "#059669",
            "maintenance": "#D97706",
        }

        lang_labels = labels.get(locale, labels["en"])
        type_label = lang_labels.get(announcement_type, lang_labels["info"])
        color = type_colors.get(announcement_type, "#4F46E5")

        subject = f"[Creator Control Center] {type_label['prefix']}: {announcement_title}"

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">{type_label['icon']} {announcement_title}</h2>
            <p>안녕하세요 {name}님,</p>
            <div style="border-left: 4px solid {color}; padding: 15px 20px; background: #f9fafb; margin: 20px 0;">
                <p style="margin: 0; line-height: 1.8; color: #374151;">{announcement_content}</p>
            </div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Creator Control Center</p>
        </div>
        """

        return self.send_email_sync(to, subject, html)

    def send_inquiry_notification(
        self,
        to: str,
        creator_name: str,
        manager_name: str,
        subject_text: str,
        message_preview: str,
        locale: str = "ko",
    ) -> EmailResult:
        """Send inquiry notification to creator."""
        templates = {
            "ko": {
                "subject": f"[Creator Control Center] 새로운 문의: {subject_text}",
                "greeting": f"안녕하세요 {creator_name}님,",
                "intro": f"{manager_name} 관리자로부터 새로운 문의가 도착했습니다.",
                "cta": "대시보드에서 확인하기",
            },
            "en": {
                "subject": f"[Creator Control Center] New Inquiry: {subject_text}",
                "greeting": f"Hello {creator_name},",
                "intro": f"You have a new inquiry from {manager_name}.",
                "cta": "View in Dashboard",
            },
            "ja": {
                "subject": f"[Creator Control Center] 新しいお問い合わせ: {subject_text}",
                "greeting": f"{creator_name}様、",
                "intro": f"{manager_name}マネージャーから新しいお問い合わせが届きました。",
                "cta": "ダッシュボードで確認",
            },
        }

        t = templates.get(locale, templates["en"])

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">💬 {subject_text}</h2>
            <p>{t['greeting']}</p>
            <p>{t['intro']}</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #555; font-style: italic;">"{message_preview[:200]}{"..." if len(message_preview) > 200 else ""}"</p>
            </div>
            <div style="text-align: center; margin: 30px 0;">
                <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">{t['cta']}</a>
            </div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Creator Control Center</p>
        </div>
        """

        return self.send_email_sync(to, t["subject"], html)

    def send_inquiry_response(
        self,
        to: str,
        creator_name: str,
        subject_text: str,
        response_text: str,
        locale: str = "ko",
    ) -> EmailResult:
        """Send inquiry response notification to creator."""
        templates = {
            "ko": {
                "subject": f"[Creator Control Center] 문의 답변: {subject_text}",
                "greeting": f"안녕하세요 {creator_name}님,",
                "intro": "귀하의 문의에 대한 답변이 도착했습니다.",
                "cta": "전체 답변 보기",
            },
            "en": {
                "subject": f"[Creator Control Center] Inquiry Response: {subject_text}",
                "greeting": f"Hello {creator_name},",
                "intro": "A response to your inquiry has been received.",
                "cta": "View Full Response",
            },
            "ja": {
                "subject": f"[Creator Control Center] お問い合わせへの回答: {subject_text}",
                "greeting": f"{creator_name}様、",
                "intro": "お問い合わせへの回答が届きました。",
                "cta": "回答を見る",
            },
        }

        t = templates.get(locale, templates["en"])

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">✉️ {subject_text}</h2>
            <p>{t['greeting']}</p>
            <p>{t['intro']}</p>
            <div style="background: #f0fdf4; border: 1px solid #22c55e; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #166534; line-height: 1.6;">{response_text[:500]}{"..." if len(response_text) > 500 else ""}</p>
            </div>
            <div style="text-align: center; margin: 30px 0;">
                <a href="/dashboard" style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold;">{t['cta']}</a>
            </div>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Creator Control Center</p>
        </div>
        """

        return self.send_email_sync(to, t["subject"], html)


# Global singleton instance
resend_email_service = ResendEmailService()
