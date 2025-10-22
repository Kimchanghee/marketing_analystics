"""Helper utilities for managing social authentication records."""

from __future__ import annotations

import logging
from typing import Iterable

from sqlmodel import Session, select

from ..models import ActivityLog, SocialAccount, SocialProvider, User

logger = logging.getLogger(__name__)


class SocialAuthService:
    SUPPORTED_PROVIDERS: tuple[SocialProvider, ...] = (
        SocialProvider.GOOGLE,
        SocialProvider.APPLE,
    )

    def get_supported_providers(self) -> Iterable[SocialProvider]:
        return self.SUPPORTED_PROVIDERS

    def link_account(
        self,
        *,
        session: Session,
        user: User,
        provider: SocialProvider,
        provider_user_id: str,
        metadata: dict | None = None,
    ) -> SocialAccount:
        """Create a SocialAccount for the user if it doesn't exist."""

        existing = session.exec(
            select(SocialAccount)
            .where(SocialAccount.provider == provider)
            .where(SocialAccount.provider_user_id == provider_user_id)
        ).first()
        if existing:
            if existing.user_id != user.id:
                raise ValueError("social_account_in_use")
            return existing

        social_account = SocialAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            metadata_json=metadata or {},
        )
        session.add(social_account)
        session.add(ActivityLog(user_id=user.id, action=f"link_{provider.value}"))
        logger.info(
            "Linked %s account %s to user_id=%s", provider.value, provider_user_id, user.id
        )
        return social_account

    def find_account(
        self, session: Session, provider: SocialProvider, provider_user_id: str
    ) -> SocialAccount | None:
        return session.exec(
            select(SocialAccount)
            .where(SocialAccount.provider == provider)
            .where(SocialAccount.provider_user_id == provider_user_id)
        ).first()


social_auth_service = SocialAuthService()
