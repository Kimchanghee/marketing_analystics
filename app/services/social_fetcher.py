from datetime import datetime, timedelta
from random import randint, random
from typing import Any, Dict, List

from ..models import ChannelAccount
from ..cache import cache
from .channel_connectors import (
    ChannelConnectorConfigError,
    ChannelConnectorError,
    get_connector,
)

PLATFORMS = [
    "instagram",
    "threads",
    "youtube",
    "twitter",
    "tiktok",
    "facebook",
    "meta_ads",
]


def generate_mock_metrics(account_name: str) -> Dict[str, str | int | float]:
    base_followers = randint(1_000, 100_000)
    growth = round(random() * 10, 2)
    engagement = round(random() * 8, 2)
    last_post = datetime.utcnow() - timedelta(hours=randint(2, 72))

    # 시간대별 조회수 데이터 생성 (24시간)
    hourly_views = []
    base_views = randint(1000, 10000)
    for hour in range(24):
        # 피크 시간대 (오후 6시-10시, 점심시간 12시-2시)에 더 높은 조회수
        if hour in [12, 13, 18, 19, 20, 21]:
            views = int(base_views * (1.5 + random() * 0.5))
        elif hour in [0, 1, 2, 3, 4, 5]:
            views = int(base_views * (0.3 + random() * 0.2))
        else:
            views = int(base_views * (0.8 + random() * 0.4))

        hourly_views.append({
            "hour": hour,
            "views": views
        })

    return {
        "account": account_name,
        "followers": base_followers,
        "growth_rate": growth,
        "engagement_rate": engagement,
        "last_post_date": last_post.isoformat(),
        "last_post_title": f"Performance update {last_post.strftime('%Y-%m-%d')}",
        "recent_posts": [
            {
                "title": f"Campaign highlight #{i+1}",
                "published_at": (last_post - timedelta(days=i)).isoformat(),
                "impressions": randint(5000, 150000),
                "likes": randint(100, 10000),
                "comments": randint(10, 500),
            }
            for i in range(3)
        ],
        "hourly_views": hourly_views,
    }


def _with_metadata(metrics: Dict[str, Any], *, source: str, error: str | None = None) -> Dict[str, Any]:
    metrics["source"] = source
    if error:
        metrics["error"] = error
    return metrics


def fetch_channel_snapshots(accounts: List[ChannelAccount]) -> Dict[int, Dict[str, Any]]:
    """채널 스냅샷 가져오기 (5분 캐싱 적용)"""
    snapshots: Dict[int, Dict[str, Any]] = {}
    for account in accounts:
        if account.id is None:
            continue

        # 캐시 키 생성
        cache_key = f"snapshot:{account.id}:{account.platform}"

        # 캐시에서 조회
        cached_snapshot = cache.get(cache_key)
        if cached_snapshot is not None:
            snapshots[account.id] = cached_snapshot
            continue

        # 캐시 미스 - 새로 가져오기
        connector = get_connector(account.platform)
        if not connector:
            metrics = generate_mock_metrics(account.account_name)
            snapshot = _with_metadata(
                metrics,
                source="mock",
                error="지원되지 않는 채널입니다.",
            )
            snapshots[account.id] = snapshot
            cache.set(cache_key, snapshot, ttl_seconds=300)  # 5분 캐싱
            continue
        try:
            metrics = connector.fetch(account)
            metrics.setdefault("recent_posts", [])
            metrics.setdefault("followers", 0)
            metrics.setdefault("growth_rate", 0.0)
            metrics.setdefault("engagement_rate", 0.0)
            metrics.setdefault("account", account.account_name)
            snapshot = _with_metadata(metrics, source="api")
            snapshots[account.id] = snapshot
            cache.set(cache_key, snapshot, ttl_seconds=300)  # 5분 캐싱
        except ChannelConnectorConfigError as exc:
            metrics = generate_mock_metrics(account.account_name)
            snapshot = _with_metadata(
                metrics,
                source="mock",
                error=str(exc),
            )
            snapshots[account.id] = snapshot
            cache.set(cache_key, snapshot, ttl_seconds=60)  # 에러는 1분만 캐싱
        except ChannelConnectorError as exc:
            metrics = generate_mock_metrics(account.account_name)
            snapshot = _with_metadata(
                metrics,
                source="mock",
                error=str(exc),
            )
            snapshots[account.id] = snapshot
            cache.set(cache_key, snapshot, ttl_seconds=60)  # 에러는 1분만 캐싱
    return snapshots
