"""Channel connector implementations for pulling live metrics from each platform."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests import Response

from ..models import ChannelAccount, ChannelCredential

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class ChannelConnectorError(Exception):
    """Base exception for connector failures."""


class ChannelConnectorConfigError(ChannelConnectorError):
    """Raised when a connector is missing mandatory configuration."""


class BaseConnector:
    platform: str

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        raise NotImplementedError

    def _ensure_credential(
        self, account: ChannelAccount, *, require_token: bool = False
    ) -> ChannelCredential:
        credential = account.credential
        if credential is None:
            raise ChannelConnectorConfigError(
                f"{account.platform} 연결에 필요한 자격 증명이 설정되지 않았습니다."
            )
        if require_token and not credential.access_token:
            raise ChannelConnectorConfigError(
                f"{account.platform} 연동에 access token이 필요합니다."
            )
        return credential

    def _http_get(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> Response:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:  # pragma: no cover - network failure
            raise ChannelConnectorError(str(exc)) from exc
        if response.status_code >= 400:
            raise ChannelConnectorError(
                f"HTTP {response.status_code} 오류 - {response.text[:200]}"
            )
        return response

    def _get_json(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        response = self._http_get(url, params=params, headers=headers)
        try:
            return response.json()
        except ValueError as exc:
            raise ChannelConnectorError("JSON 응답을 파싱할 수 없습니다.") from exc


class GraphConnector(BaseConnector):
    api_version = "v20.0"

    @property
    def base_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}"

    def _graph_get(
        self,
        path: str,
        token: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        params = params or {}
        params["access_token"] = token
        url = f"{self.base_url}/{path}"
        return self._get_json(url, params=params)


class InstagramConnector(GraphConnector):
    platform = "instagram"

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = self._ensure_credential(account, require_token=True)
        ig_business_id = credential.metadata_json.get("business_id") or credential.identifier
        if not ig_business_id:
            raise ChannelConnectorConfigError("Instagram Business ID가 필요합니다.")
        profile = self._graph_get(
            ig_business_id,
            credential.access_token or "",
            params={"fields": "username,followers_count"},
        )
        media = self._graph_get(
            f"{ig_business_id}/media",
            credential.access_token or "",
            params={
                "fields": "id,caption,like_count,comments_count,timestamp",
                "limit": 3,
            },
        )
        followers = int(profile.get("followers_count", 0))
        posts = []
        for item in media.get("data", []):
            likes = int(item.get("like_count", 0))
            comments = int(item.get("comments_count", 0))
            posts.append(
                {
                    "title": (item.get("caption") or "Instagram Post")[:80],
                    "published_at": item.get("timestamp"),
                    "impressions": likes + comments,
                    "likes": likes,
                    "comments": comments,
                }
            )
        last_post = posts[0] if posts else {}
        engagement_rate = 0.0
        if followers and posts:
            top_post = posts[0]
            engagement_rate = round(
                ((top_post.get("likes", 0) + top_post.get("comments", 0)) / followers)
                * 100,
                2,
            )
        return {
            "account": profile.get("username", account.account_name),
            "followers": followers,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)),
            "engagement_rate": engagement_rate,
            "last_post_date": last_post.get("published_at"),
            "last_post_title": last_post.get("title"),
            "recent_posts": posts,
        }


class ThreadsConnector(BaseConnector):
    platform = "threads"
    FOLLOWERS_REGEX = re.compile(r'"followers_count":(\d+)')
    POSTS_REGEX = re.compile(r'"thread_items":(\[.*?\])')

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = account.credential
        username = (credential.identifier if credential and credential.identifier else account.account_name).lstrip("@")
        response = self._http_get(
            f"https://www.threads.net/@{username}",
            headers={"User-Agent": USER_AGENT},
        )
        html = response.text
        followers = 0
        match = self.FOLLOWERS_REGEX.search(html)
        if match:
            followers = int(match.group(1))
        recent_posts: List[Dict[str, Any]] = []
        posts_match = self.POSTS_REGEX.search(html)
        if posts_match:
            try:
                data = json.loads(posts_match.group(1))
                for raw_post in data[:3]:
                    post_data = raw_post.get("post") or {}
                    title = (
                        post_data.get("caption")
                        or post_data.get("text_post_app_info", {})
                        .get("share_info", {})
                        .get("quoted_post_caption")
                    )
                    recent_posts.append(
                        {
                            "title": (title or "Threads Post")[:80],
                            "published_at": post_data.get("taken_at") or post_data.get("pk"),
                            "impressions": int(post_data.get("like_count", 0)),
                            "likes": int(post_data.get("like_count", 0)),
                            "comments": int(post_data.get("comment_count", 0)),
                        }
                    )
            except (json.JSONDecodeError, TypeError):
                recent_posts = []
        last_post = recent_posts[0] if recent_posts else {}
        engagement = 0.0
        if followers and recent_posts:
            engagement = round(
                ((recent_posts[0].get("likes", 0) + recent_posts[0].get("comments", 0)) / followers)
                * 100,
                2,
            )
        return {
            "account": username,
            "followers": followers,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)) if credential else 0.0,
            "engagement_rate": engagement,
            "last_post_date": last_post.get("published_at"),
            "last_post_title": last_post.get("title"),
            "recent_posts": recent_posts,
        }


class YouTubeConnector(BaseConnector):
    platform = "youtube"

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = self._ensure_credential(account)
        api_key = credential.access_token or credential.secret
        if not api_key:
            raise ChannelConnectorConfigError("YouTube API Key 또는 OAuth 토큰이 필요합니다.")
        identifier = (credential.identifier or account.account_name).lstrip("@")

        # 채널 기본 정보 가져오기
        params = {
            "part": "statistics,snippet",
            "forUsername": identifier,
            "key": api_key,
        }
        data = self._get_json("https://www.googleapis.com/youtube/v3/channels", params=params)
        items = data.get("items")
        if not items:
            params = {"part": "statistics,snippet", "id": identifier, "key": api_key}
            data = self._get_json(
                "https://www.googleapis.com/youtube/v3/channels", params=params
            )
            items = data.get("items", [])
        if not items:
            raise ChannelConnectorError("채널 정보를 찾을 수 없습니다.")

        channel_data = items[0]
        channel_id = channel_data.get("id")
        statistics = channel_data.get("statistics", {})
        snippet = channel_data.get("snippet", {})
        followers = int(statistics.get("subscriberCount", 0))

        # 최근 업로드 동영상 가져오기
        uploads_playlist = snippet.get("relatedPlaylists", {}).get("uploads")
        recent_posts: List[Dict[str, Any]] = []
        if uploads_playlist:
            playlist_data = self._get_json(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                params={
                    "part": "snippet,contentDetails",
                    "maxResults": 3,
                    "playlistId": uploads_playlist,
                    "key": api_key,
                },
            )
            for item in playlist_data.get("items", []):
                snippet_data = item.get("snippet", {})
                recent_posts.append(
                    {
                        "title": snippet_data.get("title"),
                        "published_at": snippet_data.get("publishedAt"),
                        "impressions": int(statistics.get("viewCount", 0)),
                        "likes": int(statistics.get("likeCount", 0)),
                        "comments": int(statistics.get("commentCount", 0)),
                    }
                )

        # YouTube Analytics API로 수익 정보 가져오기 (OAuth 토큰이 있는 경우)
        revenue_data = None
        if credential.auth_type.value == "oauth2" and credential.access_token:
            revenue_data = self._fetch_revenue_data(channel_id, credential.access_token)

        last_post = recent_posts[0] if recent_posts else {}
        engagement_rate = 0.0
        if followers and statistics.get("viewCount"):
            engagement_rate = round(
                (int(statistics.get("viewCount", 0)) / max(followers, 1)) * 100,
                2,
            )

        result = {
            "account": snippet.get("title", identifier),
            "followers": followers,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)),
            "engagement_rate": engagement_rate,
            "last_post_date": last_post.get("published_at"),
            "last_post_title": last_post.get("title"),
            "recent_posts": recent_posts,
        }

        # 수익 정보 추가
        if revenue_data:
            result["revenue"] = revenue_data

        return result

    def _fetch_revenue_data(self, channel_id: str, access_token: str) -> Optional[Dict[str, Any]]:
        """YouTube Analytics API로 예상 수익 정보 가져오기"""
        try:
            from datetime import datetime, timedelta

            # 지난 28일간의 데이터 가져오기
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=28)

            params = {
                "ids": f"channel=={channel_id}",
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "metrics": "estimatedRevenue,estimatedAdRevenue,estimatedRedPartnerRevenue",
                "dimensions": "",
            }

            headers = {"Authorization": f"Bearer {access_token}"}

            # YouTube Analytics API 엔드포인트
            response = self._http_get(
                "https://youtubeanalytics.googleapis.com/v2/reports",
                params=params,
                headers=headers,
            )

            data = response.json()

            # 수익 데이터 파싱
            if "rows" in data and len(data["rows"]) > 0:
                row = data["rows"][0]
                column_headers = data.get("columnHeaders", [])

                revenue_info = {}
                for i, header in enumerate(column_headers):
                    if i < len(row):
                        revenue_info[header["name"]] = row[i]

                return {
                    "estimated_revenue": revenue_info.get("estimatedRevenue", 0),
                    "estimated_ad_revenue": revenue_info.get("estimatedAdRevenue", 0),
                    "estimated_red_partner_revenue": revenue_info.get("estimatedRedPartnerRevenue", 0),
                    "period_days": 28,
                    "currency": "USD",  # YouTube는 기본적으로 USD로 반환
                }

            return None

        except Exception as e:
            # 수익 정보를 가져오지 못해도 다른 정보는 계속 표시
            return {"error": f"수익 정보를 가져올 수 없습니다: {str(e)}"}


class TwitterConnector(BaseConnector):
    platform = "twitter"

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = self._ensure_credential(account)
        bearer_token = credential.access_token or credential.secret
        if not bearer_token:
            raise ChannelConnectorConfigError("Twitter API Bearer token이 필요합니다.")
        username = (credential.identifier or account.account_name).lstrip("@")
        headers = {"Authorization": f"Bearer {bearer_token}"}
        user_data = self._get_json(
            f"https://api.twitter.com/2/users/by/username/{username}",
            headers=headers,
            params={"user.fields": "public_metrics"},
        )
        user = user_data.get("data", {})
        metrics = user.get("public_metrics", {})
        followers = int(metrics.get("followers_count", 0))
        tweets_data = self._get_json(
            f"https://api.twitter.com/2/users/{user.get('id')}/tweets",
            headers=headers,
            params={"max_results": 5, "tweet.fields": "created_at,public_metrics"},
        )
        recent_posts: List[Dict[str, Any]] = []
        for tweet in tweets_data.get("data", [])[:3]:
            tweet_metrics = tweet.get("public_metrics", {})
            impressions = tweet_metrics.get("impression_count") or (
                tweet_metrics.get("retweet_count", 0)
                + tweet_metrics.get("reply_count", 0)
                + tweet_metrics.get("like_count", 0)
            )
            recent_posts.append(
                {
                    "title": tweet.get("text", "Tweet")[:80],
                    "published_at": tweet.get("created_at"),
                    "impressions": int(impressions or 0),
                    "likes": int(tweet_metrics.get("like_count", 0)),
                    "comments": int(tweet_metrics.get("reply_count", 0)),
                }
            )
        last_post = recent_posts[0] if recent_posts else {}
        engagement_rate = 0.0
        if followers and recent_posts:
            top = recent_posts[0]
            engagement_rate = round(
                (top.get("likes", 0) + top.get("comments", 0)) / max(followers, 1) * 100,
                2,
            )
        return {
            "account": user.get("name", username),
            "followers": followers,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)),
            "engagement_rate": engagement_rate,
            "last_post_date": last_post.get("published_at"),
            "last_post_title": last_post.get("title"),
            "recent_posts": recent_posts,
        }


class TikTokConnector(BaseConnector):
    platform = "tiktok"
    FOLLOWERS_REGEX = re.compile(r'"followerCount":(\d+)')
    LIKES_REGEX = re.compile(r'"diggCount":(\d+)')

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = account.credential
        username = (credential.identifier if credential and credential.identifier else account.account_name).lstrip("@")
        response = self._http_get(
            f"https://www.tiktok.com/@{username}",
            headers={"User-Agent": USER_AGENT},
        )
        html = response.text
        followers = 0
        match = self.FOLLOWERS_REGEX.search(html)
        if match:
            followers = int(match.group(1))
        likes_match = self.LIKES_REGEX.findall(html)
        recent_posts: List[Dict[str, Any]] = []
        for like_count in likes_match[:3]:
            likes = int(like_count)
            recent_posts.append(
                {
                    "title": "TikTok Video",
                    "published_at": None,
                    "impressions": likes,
                    "likes": likes,
                    "comments": 0,
                }
            )
        last_post = recent_posts[0] if recent_posts else {}
        engagement = 0.0
        if followers and recent_posts:
            engagement = round((recent_posts[0]["likes"] / followers) * 100, 2)
        return {
            "account": username,
            "followers": followers,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)) if credential else 0.0,
            "engagement_rate": engagement,
            "last_post_date": last_post.get("published_at"),
            "last_post_title": last_post.get("title"),
            "recent_posts": recent_posts,
        }


class FacebookConnector(GraphConnector):
    platform = "facebook"

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = self._ensure_credential(account, require_token=True)
        page_id = credential.metadata_json.get("page_id") or credential.identifier
        if not page_id:
            raise ChannelConnectorConfigError("Facebook 페이지 ID가 필요합니다.")
        page = self._graph_get(
            page_id,
            credential.access_token or "",
            params={"fields": "name,followers_count,fan_count"},
        )
        posts = self._graph_get(
            f"{page_id}/posts",
            credential.access_token or "",
            params={"fields": "message,created_time", "limit": 3},
        )
        followers = int(page.get("followers_count") or page.get("fan_count") or 0)
        recent_posts: List[Dict[str, Any]] = []
        for post in posts.get("data", []):
            recent_posts.append(
                {
                    "title": (post.get("message") or "Facebook Post")[:80],
                    "published_at": post.get("created_time"),
                    "impressions": 0,
                    "likes": 0,
                    "comments": 0,
                }
            )
        last_post = recent_posts[0] if recent_posts else {}
        return {
            "account": page.get("name", account.account_name),
            "followers": followers,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)),
            "engagement_rate": 0.0,
            "last_post_date": last_post.get("published_at"),
            "last_post_title": last_post.get("title"),
            "recent_posts": recent_posts,
        }


class MetaAdsConnector(GraphConnector):
    platform = "meta_ads"

    def fetch(self, account: ChannelAccount) -> Dict[str, Any]:
        credential = self._ensure_credential(account, require_token=True)
        ad_account_id = credential.metadata_json.get("ad_account_id") or credential.identifier
        if not ad_account_id:
            raise ChannelConnectorConfigError("Meta Ads 계정 ID가 필요합니다.")
        insights = self._graph_get(
            f"act_{ad_account_id}/insights",
            credential.access_token or "",
            params={"fields": "spend,impressions,clicks", "date_preset": "last_7d"},
        )
        data = insights.get("data", [{}])
        summary = data[0] if data else {}
        spend = float(summary.get("spend", 0.0))
        impressions = int(summary.get("impressions", 0))
        clicks = int(summary.get("clicks", 0))
        engagement = 0.0
        if impressions:
            engagement = round((clicks / impressions) * 100, 2)
        return {
            "account": ad_account_id,
            "followers": impressions,
            "growth_rate": float(credential.metadata_json.get("growth_rate", 0.0)),
            "engagement_rate": engagement,
            "last_post_date": datetime.utcnow().isoformat(),
            "last_post_title": "최근 7일 광고 인사이트",
            "recent_posts": [
                {
                    "title": "7일간 광고 지표",
                    "published_at": datetime.utcnow().isoformat(),
                    "impressions": impressions,
                    "likes": clicks,
                    "comments": 0,
                    "spend": spend,
                }
            ],
        }


CONNECTOR_REGISTRY: Dict[str, BaseConnector] = {
    "instagram": InstagramConnector(),
    "threads": ThreadsConnector(),
    "youtube": YouTubeConnector(),
    "twitter": TwitterConnector(),
    "tiktok": TikTokConnector(),
    "facebook": FacebookConnector(),
    "meta_ads": MetaAdsConnector(),
}


def get_connector(platform: str) -> Optional[BaseConnector]:
    return CONNECTOR_REGISTRY.get(platform)
