"""Utilities for issuing and validating email verification codes."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlmodel import select

from ..config import get_settings
from ..database import session_context
from ..models import EmailVerification
from .resend_email import resend_email_service

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Manage verification codes used during signup or security checks."""

    # Max verification attempts before lockout
    MAX_ATTEMPTS = 5
    # Lockout duration after max attempts (minutes)
    LOCKOUT_MINUTES = 15

    def __init__(self) -> None:
        settings = get_settings()
        self.code_length = getattr(settings, "verification_code_length", 6)
        expiry_minutes = getattr(settings, "verification_code_expiry_minutes", 15)
        self.expiry_delta = timedelta(minutes=expiry_minutes)

    def _generate_code(self) -> str:
        """Generate a cryptographically secure verification code."""
        # Use secrets module for cryptographically secure random numbers
        return "".join(str(secrets.randbelow(10)) for _ in range(self.code_length))

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def request_code(self, email: str, locale: str = "ko") -> str:
        """Create (or refresh) a verification code for the supplied email.

        The plain code is returned so the caller can relay it via email/SMS.
        The implementation simply logs it which makes future integrations easy.
        """

        code = self._generate_code()
        hashed = self._hash_code(code)
        expires_at = datetime.utcnow() + self.expiry_delta

        with session_context() as session:
            record = session.exec(
                select(EmailVerification).where(EmailVerification.email == email)
            ).first()
            if record:
                record.code_hash = hashed
                record.verified = False
                record.expires_at = expires_at
                record.locale = locale
                record.attempt_count = 0
            else:
                record = EmailVerification(
                    email=email,
                    code_hash=hashed,
                    locale=locale,
                    expires_at=expires_at,
                )
                session.add(record)
            session.commit()

        logger.info("Generated verification code for %s (expires at %s)", email, expires_at)

        # Resend를 통해 이메일 발송
        settings = get_settings()
        if settings.use_resend:
            result = resend_email_service.send_verification_code(email, code, locale)
            if result.success:
                logger.info("Verification code email sent via Resend to %s", email)
            else:
                logger.warning("Failed to send verification code email via Resend: %s", result.error)

        return code

    def verify_code(self, email: str, code: str) -> bool:
        """Validate the given verification code.

        Returns True when the code is valid and marks the record as verified.
        Returns False if code is invalid, expired, or max attempts exceeded.
        """

        hashed = self._hash_code(code)
        with session_context() as session:
            record = session.exec(
                select(EmailVerification).where(EmailVerification.email == email)
            ).first()
            if not record:
                return False
            if record.expires_at < datetime.utcnow():
                return False
            # Check if max attempts exceeded (lockout)
            if record.attempt_count >= self.MAX_ATTEMPTS:
                # Check if lockout period has passed since last attempt
                lockout_until = record.expires_at + timedelta(minutes=self.LOCKOUT_MINUTES)
                if datetime.utcnow() < lockout_until:
                    logger.warning(
                        "Verification attempt blocked for %s due to max attempts exceeded",
                        email
                    )
                    return False
                # Lockout expired, reset attempt count
                record.attempt_count = 0
            if record.code_hash != hashed:
                record.attempt_count += 1
                session.add(record)
                session.commit()
                logger.info(
                    "Invalid verification code for %s (attempt %d/%d)",
                    email, record.attempt_count, self.MAX_ATTEMPTS
                )
                return False
            record.verified = True
            record.attempt_count = 0
            session.add(record)
            session.commit()
        return True

    def clear_code(self, email: str) -> None:
        with session_context() as session:
            record = session.exec(
                select(EmailVerification).where(EmailVerification.email == email)
            ).first()
            if record:
                session.delete(record)
                session.commit()


email_verification_service = EmailVerificationService()
