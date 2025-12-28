"""
소셜 미디어 서비스 모듈

이 모듈은 모든 소셜 미디어 관련 기능을 제공합니다:
- 소셜 인증 (OAuth)
- 소셜 데이터 수집
- 채널 연동 (Instagram, YouTube, TikTok 등)
"""

from .social_auth import social_auth_service
from .social_oauth import (
    get_oauth_client,
    OAuthError,
    SocialOAuthNotConfigured,
)
from .social_fetcher import fetch_channel_snapshots, generate_mock_metrics
from .channel_connectors import (
    InstagramConnector,
    YouTubeConnector,
    TikTokConnector,
)

__all__ = [
    "social_auth_service",
    "get_oauth_client",
    "OAuthError",
    "SocialOAuthNotConfigured",
    "fetch_channel_snapshots",
    "generate_mock_metrics",
    "InstagramConnector",
    "YouTubeConnector",
    "TikTokConnector",
]
