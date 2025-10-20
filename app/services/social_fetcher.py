from datetime import datetime, timedelta
from random import randint, random
from typing import Dict, List

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
    }


def fetch_channel_snapshots(accounts: List[Dict[str, str]]) -> Dict[str, Dict[str, str | int | float]]:
    snapshots: Dict[str, Dict[str, str | int | float]] = {}
    for account in accounts:
        platform = account.get("platform", "unknown")
        account_name = account.get("account_name", "")
        snapshots[platform] = generate_mock_metrics(account_name)
    return snapshots
