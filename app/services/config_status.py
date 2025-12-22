"""Configuration status service."""

from ..config import get_settings


def get_config_status() -> dict:
    """Get configuration status."""
    settings = get_settings()

    status = {
        "database": {
            "configured": bool(
                settings.database_url and "postgresql" in settings.database_url
            ),
            "type": (
                "postgresql"
                if "postgresql" in (settings.database_url or "")
                else "sqlite"
            ),
        },
        "email": {
            "configured": bool(
                settings.super_admin_email and settings.super_admin_email_password
            ),
            "service": (
                "gmail"
                if "@gmail.com" in (settings.super_admin_email or "")
                else "custom"
            ),
        },
        "ai": {
            "configured": bool(
                settings.gemini_api_key and settings.gemini_api_key.strip()
            ),
            "service": "gemini",
        },
        "oauth": {
            "google": bool(
                settings.google_client_id and settings.google_client_secret
            ),
            "facebook": bool(
                settings.facebook_app_id and settings.facebook_app_secret
            ),
            "twitter": bool(
                settings.twitter_client_id and settings.twitter_client_secret
            ),
            "tiktok": bool(
                settings.tiktok_client_key and settings.tiktok_client_secret
            ),
            "apple": bool(
                settings.apple_client_id
                and settings.apple_team_id
                and settings.apple_key_id
                and settings.apple_private_key
            ),
        },
        "environment": settings.environment,
    }

    return status


def get_missing_configs() -> list:
    """Get list of missing configurations."""
    status = get_config_status()
    missing = []

    if not status["email"]["configured"]:
        missing.append(
            {
                "name": "Email Service",
                "description": "Super admin email feature unavailable",
                "env_vars": ["SUPER_ADMIN_EMAIL", "SUPER_ADMIN_EMAIL_PASSWORD"],
                "docs_url": "https://support.google.com/accounts/answer/185833",
            }
        )

    if not status["ai"]["configured"]:
        missing.append(
            {
                "name": "AI Service (Gemini)",
                "description": "AI PD feature unavailable",
                "env_vars": ["GEMINI_API_KEY"],
                "docs_url": "https://ai.google.dev/gemini-api/docs",
            }
        )

    oauth_missing = []
    if not status["oauth"]["google"]:
        oauth_missing.append("Google")
    if not status["oauth"]["facebook"]:
        oauth_missing.append("Facebook")
    if not status["oauth"]["twitter"]:
        oauth_missing.append("Twitter/X")
    if not status["oauth"]["tiktok"]:
        oauth_missing.append("TikTok")
    if not status["oauth"]["apple"]:
        oauth_missing.append("Apple")

    if oauth_missing:
        missing.append(
            {
                "name": "Social Login",
                "description": f"{', '.join(oauth_missing)} social login unavailable",
                "env_vars": [
                    "GOOGLE_CLIENT_ID",
                    "GOOGLE_CLIENT_SECRET",
                    "FACEBOOK_APP_ID",
                    "FACEBOOK_APP_SECRET",
                    "TWITTER_CLIENT_ID",
                    "TWITTER_CLIENT_SECRET",
                    "TIKTOK_CLIENT_KEY",
                    "TIKTOK_CLIENT_SECRET",
                    "APPLE_CLIENT_ID",
                    "APPLE_TEAM_ID",
                    "APPLE_KEY_ID",
                    "APPLE_PRIVATE_KEY",
                ],
                "docs_url": "https://developers.google.com/identity/protocols/oauth2",
            }
        )

    return missing


def get_config_summary() -> dict:
    """Get configuration summary."""
    status = get_config_status()
    missing = get_missing_configs()

    return {
        "status": status,
        "missing": missing,
        "total_missing": len(missing),
        "is_production": status["environment"].lower() == "production",
        "has_essential": status["database"]["configured"],
        "has_email": status["email"]["configured"],
        "has_ai": status["ai"]["configured"],
        "has_oauth": any(
            [
                status["oauth"]["google"],
                status["oauth"]["facebook"],
                status["oauth"]["twitter"],
                status["oauth"]["tiktok"],
                status["oauth"]["apple"],
            ]
        ),
    }
