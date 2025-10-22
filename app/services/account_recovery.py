"""Account recovery helpers for password resets and username reminders."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from sqlmodel import select

from ..auth import auth_manager
from ..config import get_settings
from ..database import get_session
from ..models import PasswordResetToken, User

logger = logging.getLogger(__name__)


class AccountRecoveryService:
    def __init__(self) -> None:
        settings = get_settings()
        expiry_minutes = getattr(settings, "password_reset_token_expiry_minutes", 30)
        self.expiry_delta = timedelta(minutes=expiry_minutes)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_reset_token(self, user: User) -> str:
        """Create a password reset token for the user and persist it."""

        token = secrets.token_urlsafe(32)
        hashed = self._hash_token(token)
        expires_at = datetime.utcnow() + self.expiry_delta

        with get_session() as session:
            record = PasswordResetToken(
                user_id=user.id,
                token_hash=hashed,
                expires_at=expires_at,
            )
            session.add(record)
            session.commit()

        logger.info("Created password reset token for user_id=%s expiring at %s", user.id, expires_at)
        return token

    def verify_and_consume_token(self, user: User, token: str) -> bool:
        hashed = self._hash_token(token)
        with get_session() as session:
            record = session.exec(
                select(PasswordResetToken)
                .where(PasswordResetToken.user_id == user.id)
                .where(PasswordResetToken.token_hash == hashed)
                .where(PasswordResetToken.used.is_(False))
            ).first()
            if not record:
                return False
            if record.expires_at < datetime.utcnow():
                return False
            record.used = True
            session.add(record)
            session.commit()
        return True

    def reset_password(self, user: User, token: str, new_password: str) -> bool:
        if not self.verify_and_consume_token(user, token):
            return False
        hashed = auth_manager.hash_password(new_password)
        with get_session() as session:
            db_user = session.exec(select(User).where(User.id == user.id)).first()
            if not db_user:
                return False
            db_user.hashed_password = hashed
            db_user.password_login_enabled = True
            db_user.password_set_at = datetime.utcnow()
            session.add(db_user)
            session.commit()
        logger.info("Password reset for user_id=%s", user.id)
        return True

    def remind_username(self, email: str) -> bool:
        with get_session() as session:
            exists = session.exec(select(User).where(User.email == email)).first()
        if exists:
            logger.info("Username reminder requested for %s", email)
            return True
        return False


account_recovery_service = AccountRecoveryService()
