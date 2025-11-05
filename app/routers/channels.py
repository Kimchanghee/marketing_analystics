"""채널 관리 및 OAuth 인증 라우터"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlencode, quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from ..auth import create_access_token
from ..database import get_session
from ..dependencies import get_current_user, require_roles
from ..models import (
    AuthType,
    ChannelAccount,
    ChannelCredential,
    Subscription,
    User,
    UserRole,
)
from ..services.localization import load_translations
from ..services.social_fetcher import fetch_channel_snapshots

router = APIRouter(prefix="/channels", tags=["channels"])


def get_oauth_configs():
    """OAuth 설정을 동적으로 가져오기 (환경변수 로드)"""
    from ..config import settings

    return {
        "instagram": {
            "provider": "facebook",
            "auth_url": "https://www.facebook.com/v20.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
            "scope": "instagram_basic,instagram_manage_insights,pages_show_list,pages_read_engagement",
            "client_id": settings.facebook_app_id,
            "client_secret": settings.facebook_app_secret,
        },
        "facebook": {
            "provider": "facebook",
            "auth_url": "https://www.facebook.com/v20.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
            "scope": "pages_show_list,pages_read_engagement,pages_read_user_content,read_insights",
            "client_id": settings.facebook_app_id,
            "client_secret": settings.facebook_app_secret,
        },
        "threads": {
            "provider": "facebook",
            "auth_url": "https://www.facebook.com/v20.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
            "scope": "threads_basic,threads_content_publish,threads_manage_insights",
            "client_id": settings.facebook_app_id,
            "client_secret": settings.facebook_app_secret,
        },
        "youtube": {
            "provider": "google",
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scope": "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
        },
        "twitter": {
            "provider": "twitter",
            "auth_url": "https://twitter.com/i/oauth2/authorize",
            "token_url": "https://api.twitter.com/2/oauth2/token",
            "scope": "tweet.read users.read follows.read offline.access",
            "client_id": settings.twitter_client_id,
            "client_secret": settings.twitter_client_secret,
        },
        "tiktok": {
            "provider": "tiktok",
            "auth_url": "https://www.tiktok.com/v2/auth/authorize",
            "token_url": "https://open.tiktokapis.com/v2/oauth/token/",
            "scope": "user.info.basic,video.list,video.insights",
            "client_id": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
        },
    }


@router.get("/manage", response_class=HTMLResponse)
async def manage_channels(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """채널 관리 페이지"""
    # 사용자의 현재 채널들 가져오기
    channels = session.exec(
        select(ChannelAccount).where(ChannelAccount.owner_id == user.id)
    ).all()

    # 구독 정보 가져오기
    subscription = session.exec(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.active == True
        )
    ).first()

    if not subscription:
        subscription = Subscription(
            user_id=user.id,
            tier="free",
            max_accounts=1
        )
        session.add(subscription)
        session.commit()

    # 번역 로드 및 실시간 스냅샷 준비
    strings = load_translations(user.locale)
    channel_snapshots = fetch_channel_snapshots(channels)

    platform_section = strings.get("channels_manage", {}).get("platforms", {})
    platform_items = platform_section.get("items", {})
    platform_order = platform_section.get("order") or list(platform_items.keys())
    platform_features = platform_section.get("feature_points", [])
    plan_label = strings.get("subscriptions", {}).get(
        subscription.tier.value, subscription.tier.value.title()
    )
    limit_reached = len(channels) >= subscription.max_accounts

    # 각 채널의 연결 상태 확인
    channel_status = []
    for channel in channels:
        has_credential = channel.credential is not None
        is_connected = False
        needs_refresh = False

        if has_credential and channel.credential:
            is_connected = channel.credential.access_token_encrypted is not None
            if channel.credential.expires_at:
                needs_refresh = channel.credential.expires_at < datetime.utcnow()

        channel_status.append({
            "channel": channel,
            "is_connected": is_connected,
            "needs_refresh": needs_refresh,
        })

    # 지원하는 플랫폼 목록
    platforms = [
        {
            "id": "instagram",
            "name": "Instagram",
            "icon": "📷",
            "color": "#E4405F",
            "description": "게시물, 스토리, 릴스 분석",
        },
        {
            "id": "facebook",
            "name": "Facebook",
            "icon": "📘",
            "color": "#1877F2",
            "description": "페이지 인사이트 및 게시물 분석",
        },
        {
            "id": "threads",
            "name": "Threads",
            "icon": "🧵",
            "color": "#000000",
            "description": "스레드 게시물 및 참여도 분석",
        },
        {
            "id": "youtube",
            "name": "YouTube",
            "icon": "▶️",
            "color": "#FF0000",
            "description": "동영상, 구독자, 시청 시간 분석",
        },
        {
            "id": "twitter",
            "name": "Twitter / X",
            "icon": "🐦",
            "color": "#1DA1F2",
            "description": "트윗, 팔로워, 참여도 분석",
        },
        {
            "id": "tiktok",
            "name": "TikTok",
            "icon": "🎵",
            "color": "#000000",
            "description": "동영상, 좋아요, 조회수 분석",
        },
    ]

    platforms = [
        {
            "id": platform_id,
            "badge": platform_items.get(platform_id, {}).get("badge", platform_id[:2].upper()),
        }
        for platform_id in platform_order
    ]

    return request.app.state.templates.TemplateResponse(
        "channels_manage.html",
        {
            "request": request,
            "user": user,
            "channels": channel_status,
            "platforms": platforms,
            "subscription": subscription,
            "max_channels": subscription.max_accounts,
            "current_channel_count": len(channels),
            "t": strings,
            "channel_snapshots": channel_snapshots,
            "platform_order": platform_order,
            "platform_features": platform_features,
            "plan_label": plan_label,
            "limit_reached": limit_reached,
        },
    )


@router.get("/connect/{platform}")
async def connect_channel(
    platform: str,
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """OAuth 인증 시작"""
    OAUTH_CONFIGS = get_oauth_configs()

    if platform not in OAUTH_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 플랫폼: {platform}"
        )

    # 구독 한도 확인
    subscription = session.exec(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.active == True
        )
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="활성 구독이 없습니다."
        )

    current_channels = session.exec(
        select(ChannelAccount).where(ChannelAccount.owner_id == user.id)
    ).all()

    if len(current_channels) >= subscription.max_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"채널 연결 한도({subscription.max_accounts}개)에 도달했습니다. 구독을 업그레이드하세요."
        )

    config = OAUTH_CONFIGS[platform]

    # 리다이렉트 URI 생성
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/channels/callback/{platform}"

    # State 파라미터 생성 (CSRF 방지)
    state = create_access_token(
        data={"user_id": user.id, "platform": platform},
        expires_delta=timedelta(minutes=10)
    )

    # OAuth 인증 URL 생성
    params = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "scope": config["scope"],
        "response_type": "code",
        "state": state,
    }

    # Twitter는 추가 파라미터 필요
    if platform == "twitter":
        params["code_challenge"] = "challenge"  # PKCE 필요시 구현
        params["code_challenge_method"] = "plain"

    auth_url = f"{config['auth_url']}?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """OAuth 콜백 처리"""
    OAUTH_CONFIGS = get_oauth_configs()

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth 인증 실패: {error}"
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 코드 또는 state가 없습니다."
        )

    # State 검증 및 사용자 정보 추출
    try:
        from ..auth import decode_token
        payload = decode_token(state)
        user_id = payload.get("user_id")
        platform_from_state = payload.get("platform")

        if platform != platform_from_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="플랫폼 불일치"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 state"
        )

    # 사용자 조회
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    config = OAUTH_CONFIGS[platform]

    # 액세스 토큰 교환
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/channels/callback/{platform}"

    import requests

    token_data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(config["token_url"], data=token_data, timeout=10)
        response.raise_for_status()
        token_response = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"토큰 교환 실패: {str(e)}"
        )

    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in", 3600)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="액세스 토큰을 받지 못했습니다."
        )

    # 플랫폼별 계정 정보 가져오기
    account_info = await _fetch_account_info(platform, access_token, config)

    # 채널 계정 생성 또는 업데이트
    existing_channel = session.exec(
        select(ChannelAccount).where(
            ChannelAccount.owner_id == user.id,
            ChannelAccount.platform == platform,
            ChannelAccount.account_name == account_info["username"]
        )
    ).first()

    if existing_channel:
        channel = existing_channel
    else:
        channel = ChannelAccount(
            owner_id=user.id,
            platform=platform,
            account_name=account_info["username"],
            followers=account_info.get("followers", 0),
        )
        session.add(channel)
        session.commit()
        session.refresh(channel)

    # 자격 증명 생성 또는 업데이트
    if channel.credential:
        credential = channel.credential
    else:
        credential = ChannelCredential(channel_id=channel.id, auth_type=AuthType.OAUTH2)
        session.add(credential)

    credential.access_token = access_token
    if refresh_token:
        credential.refresh_token = refresh_token
    credential.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    credential.identifier = account_info.get("id", account_info["username"])
    credential.metadata_json = account_info.get("metadata", {})

    session.commit()

    # 채널 관리 페이지로 리다이렉트
    return RedirectResponse(
        url="/channels/manage?success=true",
        status_code=status.HTTP_302_FOUND
    )


async def _fetch_account_info(platform: str, access_token: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """플랫폼별 계정 정보 가져오기"""
    import requests

    headers = {"Authorization": f"Bearer {access_token}"}

    if platform in ["instagram", "facebook", "threads"]:
        # Meta 플랫폼
        response = requests.get(
            "https://graph.facebook.com/v20.0/me",
            params={"fields": "id,name", "access_token": access_token},
            timeout=10
        )
        data = response.json()

        if platform == "instagram":
            # Instagram Business 계정 정보 가져오기
            accounts_response = requests.get(
                "https://graph.facebook.com/v20.0/me/accounts",
                params={"access_token": access_token},
                timeout=10
            )
            accounts = accounts_response.json().get("data", [])

            # 첫 번째 페이지의 Instagram Business 계정 찾기
            for page in accounts:
                page_id = page.get("id")
                ig_response = requests.get(
                    f"https://graph.facebook.com/v20.0/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": access_token
                    },
                    timeout=10
                )
                ig_data = ig_response.json()
                if "instagram_business_account" in ig_data:
                    ig_account_id = ig_data["instagram_business_account"]["id"]

                    # Instagram 계정 세부 정보
                    ig_detail_response = requests.get(
                        f"https://graph.facebook.com/v20.0/{ig_account_id}",
                        params={
                            "fields": "username,followers_count",
                            "access_token": access_token
                        },
                        timeout=10
                    )
                    ig_detail = ig_detail_response.json()

                    return {
                        "id": ig_account_id,
                        "username": ig_detail.get("username", "instagram_user"),
                        "followers": ig_detail.get("followers_count", 0),
                        "metadata": {"business_id": ig_account_id, "page_id": page_id}
                    }

            # Instagram 계정을 찾지 못한 경우
            return {
                "id": data.get("id", ""),
                "username": data.get("name", "instagram_user"),
                "followers": 0,
                "metadata": {}
            }

        elif platform == "facebook":
            # Facebook 페이지 정보
            accounts_response = requests.get(
                "https://graph.facebook.com/v20.0/me/accounts",
                params={"access_token": access_token},
                timeout=10
            )
            accounts = accounts_response.json().get("data", [])

            if accounts:
                page = accounts[0]  # 첫 번째 페이지 사용
                page_id = page.get("id")

                # 페이지 세부 정보
                page_response = requests.get(
                    f"https://graph.facebook.com/v20.0/{page_id}",
                    params={
                        "fields": "name,followers_count,fan_count",
                        "access_token": access_token
                    },
                    timeout=10
                )
                page_data = page_response.json()

                return {
                    "id": page_id,
                    "username": page_data.get("name", "facebook_page"),
                    "followers": page_data.get("followers_count", page_data.get("fan_count", 0)),
                    "metadata": {"page_id": page_id}
                }

        # Threads (기본 Facebook 정보 사용)
        return {
            "id": data.get("id", ""),
            "username": data.get("name", "threads_user"),
            "followers": 0,
            "metadata": {}
        }

    elif platform == "youtube":
        # YouTube
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={
                "part": "snippet,statistics",
                "mine": "true",
                "access_token": access_token
            },
            timeout=10
        )
        data = response.json()
        items = data.get("items", [])

        if items:
            channel = items[0]
            return {
                "id": channel["id"],
                "username": channel["snippet"]["title"],
                "followers": int(channel["statistics"].get("subscriberCount", 0)),
                "metadata": {"channel_id": channel["id"]}
            }

        return {"id": "", "username": "youtube_channel", "followers": 0, "metadata": {}}

    elif platform == "twitter":
        # Twitter
        response = requests.get(
            "https://api.twitter.com/2/users/me",
            params={"user.fields": "public_metrics,username"},
            headers=headers,
            timeout=10
        )
        data = response.json().get("data", {})

        return {
            "id": data.get("id", ""),
            "username": data.get("username", "twitter_user"),
            "followers": data.get("public_metrics", {}).get("followers_count", 0),
            "metadata": {"user_id": data.get("id")}
        }

    elif platform == "tiktok":
        # TikTok
        response = requests.get(
            "https://open.tiktokapis.com/v2/user/info/",
            params={"fields": "open_id,union_id,avatar_url,display_name"},
            headers=headers,
            timeout=10
        )
        data = response.json().get("data", {}).get("user", {})

        return {
            "id": data.get("open_id", ""),
            "username": data.get("display_name", "tiktok_user"),
            "followers": 0,  # TikTok API는 별도 요청 필요
            "metadata": {"open_id": data.get("open_id")}
        }

    return {"id": "", "username": "unknown", "followers": 0, "metadata": {}}


@router.post("/disconnect/{channel_id}")
async def disconnect_channel(
    channel_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """채널 연결 해제"""
    channel = session.get(ChannelAccount, channel_id)

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채널을 찾을 수 없습니다."
        )

    if channel.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 채널에 대한 권한이 없습니다."
        )

    # 채널 삭제 (cascade로 credential도 삭제됨)
    session.delete(channel)
    session.commit()

    return {"success": True, "message": "채널이 연결 해제되었습니다."}


@router.post("/refresh/{channel_id}")
async def refresh_channel_token(
    channel_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """만료된 토큰 갱신"""
    OAUTH_CONFIGS = get_oauth_configs()

    channel = session.get(ChannelAccount, channel_id)

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채널을 찾을 수 없습니다."
        )

    if channel.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 채널에 대한 권한이 없습니다."
        )

    if not channel.credential or not channel.credential.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="갱신 토큰이 없습니다. 다시 연결하세요."
        )

    config = OAUTH_CONFIGS.get(channel.platform)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 플랫폼입니다."
        )

    import requests

    token_data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "refresh_token": channel.credential.refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        response = requests.post(config["token_url"], data=token_data, timeout=10)
        response.raise_for_status()
        token_response = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"토큰 갱신 실패: {str(e)}"
        )

    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    expires_in = token_response.get("expires_in", 3600)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 액세스 토큰을 받지 못했습니다."
        )

    # 자격 증명 업데이트
    channel.credential.access_token = access_token
    if refresh_token:
        channel.credential.refresh_token = refresh_token
    channel.credential.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    session.commit()

    return {"success": True, "message": "토큰이 갱신되었습니다."}
