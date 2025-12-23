from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from authlib.integrations.starlette_client import OAuth, OAuthError
from jose import jwt

from ..config import get_settings


class SocialOAuthNotConfigured(RuntimeError):
    """Raised when a requested social provider is missing configuration."""


oauth = OAuth()

_registered_providers: set[str] = set()


def _normalize_private_key(raw_key: str) -> str:
    key = raw_key.strip()
    if "BEGIN" in key:
        return key
    # Assume base64 body without PEM markers
    header = "-----BEGIN PRIVATE KEY-----"
    footer = "-----END PRIVATE KEY-----"
    return f"{header}\n{key}\n{footer}"


def _generate_apple_client_secret() -> str:
    settings = get_settings()
    if not all(
        [
            settings.apple_client_id,
            settings.apple_team_id,
            settings.apple_key_id,
            settings.apple_private_key,
        ]
    ):
        raise SocialOAuthNotConfigured(
            "Apple Sign-In requires APPLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, and APPLE_PRIVATE_KEY"
        )

    now = datetime.utcnow()
    payload = {
        "iss": settings.apple_team_id,
        "iat": now,
        "exp": now + timedelta(minutes=30),
        "aud": "https://appleid.apple.com",
        "sub": settings.apple_client_id,
    }
    headers = {"kid": settings.apple_key_id, "alg": "ES256"}
    private_key = _normalize_private_key(settings.apple_private_key)
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def _register_google() -> None:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise SocialOAuthNotConfigured(
            "Google OAuth requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
        )
    if "google" in _registered_providers:
        return

    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    _registered_providers.add("google")


def _register_apple() -> None:
    if "apple" in _registered_providers:
        return

    settings = get_settings()
    if not settings.apple_client_id:
        raise SocialOAuthNotConfigured("Apple Sign-In requires APPLE_CLIENT_ID")

    oauth.register(
        name="apple",
        client_id=settings.apple_client_id,
        client_secret_generator=_generate_apple_client_secret,
        authorize_url="https://appleid.apple.com/auth/authorize",
        access_token_url="https://appleid.apple.com/auth/token",
        client_kwargs={
            "scope": "name email",
            "response_mode": "form_post",
            "response_type": "code",
        },
    )
    _registered_providers.add("apple")


def ensure_provider_registered(provider: str) -> None:
    if provider == "google":
        _register_google()
    elif provider == "apple":
        _register_apple()
    else:
        raise SocialOAuthNotConfigured(f"Unsupported provider: {provider}")


def get_oauth_client(provider: str):
    ensure_provider_registered(provider)
    client = oauth.create_client(provider)
    if client is None:
        raise SocialOAuthNotConfigured(f"Provider not configured: {provider}")
    return client


__all__ = [
    "oauth",
    "OAuthError",
    "get_oauth_client",
    "SocialOAuthNotConfigured",
]
