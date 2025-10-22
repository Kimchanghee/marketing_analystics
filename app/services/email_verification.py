"""Utilities for issuing and validating email verification codes."""

from __future__ import annotations

import hashlib
import logging
import random
import string
from datetime import datetime, timedelta

from sqlmodel import select

from ..config import get_settings
from ..database import get_session
from ..models import EmailVerification

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Manage verification codes used during signup or security checks."""

    def __init__(self) -> None:
        settings = get_settings()
        self.code_length = getattr(settings, "verification_code_length", 6)
        expiry_minutes = getattr(settings, "verification_code_expiry_minutes", 15)
        self.expiry_delta = timedelta(minutes=expiry_minutes)

    def _generate_code(self) -> str:
        return "".join(random.choices(string.digits, k=self.code_length))

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

        with get_session() as session:
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
        return code

    def verify_code(self, email: str, code: str) -> bool:
        """Validate the given verification code.

        Returns True when the code is valid and marks the record as verified.
        """

        hashed = self._hash_code(code)
        with get_session() as session:
            record = session.exec(
                select(EmailVerification).where(EmailVerification.email == email)
            ).first()
            if not record:
                return False
            if record.expires_at < datetime.utcnow():
                return False
            if record.code_hash != hashed:
                record.attempt_count += 1
                session.add(record)
                session.commit()
                return False
            record.verified = True
            record.attempt_count = 0
            session.add(record)
            session.commit()
        return True

    def clear_code(self, email: str) -> None:
        with get_session() as session:
            record = session.exec(
                select(EmailVerification).where(EmailVerification.email == email)
            ).first()
            if record:
                session.delete(record)
                session.commit()


email_verification_service = EmailVerificationService()
