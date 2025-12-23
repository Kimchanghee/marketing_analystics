"""
AI 기반 광고 및 콘텐츠 추천 서비스

규칙 기반 AI 시스템으로 채널 성과를 분석하고 실행 가능한 추천을 제공합니다.
"""

from datetime import datetime
from typing import Any, Dict, List


def generate_ad_recommendations(snapshot: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    채널 데이터를 분석하여 광고 추천 생성

    Args:
        snapshot: 채널 스냅샷 데이터 (followers, growth_rate, engagement_rate, recent_posts 등)

    Returns:
        추천 리스트 [{"type": "...", "priority": "...", "action": "...", "reason": "..."}]
    """
    recommendations = []

    followers = snapshot.get("followers", 0)
    growth_rate = snapshot.get("growth_rate", 0)
    engagement_rate = snapshot.get("engagement_rate", 0)
    recent_posts = snapshot.get("recent_posts", [])

    # 1. 성장률 기반 추천
    if growth_rate > 5:
        recommendations.append({
            "type": "scale",
            "priority": "high",
            "action": "광고 예산 증액",
            "reason": f"성장률 {growth_rate}%로 상승 추세입니다. 이 기회를 활용해 광고 예산을 20-30% 증액하여 성장을 가속화하세요."
        })
    elif growth_rate < -2:
        recommendations.append({
            "type": "optimize",
            "priority": "high",
            "action": "타깃 재설정",
            "reason": f"성장률 {growth_rate}%로 하락 중입니다. 현재 타깃 오디언스와 광고 소재를 재검토하고 A/B 테스트를 진행하세요."
        })
    elif 0 <= growth_rate <= 2:
        recommendations.append({
            "type": "test",
            "priority": "medium",
            "action": "새로운 콘텐츠 형식 테스트",
            "reason": f"성장률 {growth_rate}%로 정체 중입니다. 쇼츠, 릴스, 라이브 방송 등 새로운 형식을 시도해보세요."
        })

    # 2. 참여율 기반 추천
    if engagement_rate > 5:
        recommendations.append({
            "type": "scale",
            "priority": "high",
            "action": "참여형 캠페인 확대",
            "reason": f"참여율 {engagement_rate}%로 매우 높습니다. 현재 콘텐츠 스타일을 유지하면서 게시 빈도를 높이세요."
        })
    elif engagement_rate < 1:
        recommendations.append({
            "type": "optimize",
            "priority": "high",
            "action": "콘텐츠 품질 개선",
            "reason": f"참여율 {engagement_rate}%로 낮습니다. 시청자 피드백을 분석하고, 더 인터랙티브한 콘텐츠를 제작하세요."
        })

    # 3. 게시물 성과 분석
    if recent_posts:
        total_likes = sum(post.get("likes", 0) for post in recent_posts)
        total_comments = sum(post.get("comments", 0) for post in recent_posts)
        avg_likes = total_likes / len(recent_posts) if recent_posts else 0
        avg_comments = total_comments / len(recent_posts) if recent_posts else 0

        # 최근 게시물 중 성과가 좋은 것 찾기
        best_post = max(recent_posts, key=lambda p: p.get("likes", 0) + p.get("comments", 0) * 5)
        best_engagement = best_post.get("likes", 0) + best_post.get("comments", 0) * 5

        if avg_likes > 1000:
            recommendations.append({
                "type": "content",
                "priority": "medium",
                "action": "인기 콘텐츠 패턴 분석",
                "reason": f"최근 게시물의 평균 좋아요 수가 {int(avg_likes):,}개입니다. '{best_post.get('title', '최고 성과 게시물')}'과 유사한 주제와 형식을 더 만들어보세요."
            })

        if avg_comments > 50:
            recommendations.append({
                "type": "community",
                "priority": "medium",
                "action": "커뮤니티 활성화 집중",
                "reason": f"평균 댓글 수 {int(avg_comments)}개로 활발한 토론이 일어나고 있습니다. 댓글에 적극 답변하고 Q&A 콘텐츠를 기획하세요."
            })

    # 4. 시간대별 조회수 분석 (있는 경우)
    hourly_views = snapshot.get("hourly_views", [])
    if hourly_views:
        # 피크 시간대 찾기
        peak_hour = max(hourly_views, key=lambda h: h.get("views", 0))
        peak_views = peak_hour.get("views", 0)
        peak_time = peak_hour.get("hour", 0)

        avg_views = sum(h.get("views", 0) for h in hourly_views) / len(hourly_views) if hourly_views else 0

        if peak_views > avg_views * 1.5:
            recommendations.append({
                "type": "timing",
                "priority": "high",
                "action": "최적 시간대에 게시",
                "reason": f"{peak_time}시에 조회수가 가장 높습니다({int(peak_views):,}회). 이 시간대에 맞춰 콘텐츠를 게시하세요."
            })

    # 5. 팔로워 규모 기반 추천
    if followers < 1000:
        recommendations.append({
            "type": "growth",
            "priority": "medium",
            "action": "초기 성장 전략 실행",
            "reason": "팔로워가 1,000명 미만입니다. 해시태그 최적화, 다른 크리에이터와 협업, 일관된 게시 스케줄을 유지하세요."
        })
    elif 1000 <= followers < 10000:
        recommendations.append({
            "type": "monetization",
            "priority": "medium",
            "action": "수익화 준비",
            "reason": f"팔로워 {int(followers):,}명으로 수익화 단계에 진입했습니다. 브랜드 협찬, 제휴 마케팅을 고려하세요."
        })
    elif followers >= 10000:
        recommendations.append({
            "type": "brand",
            "priority": "high",
            "action": "브랜드 파트너십 확대",
            "reason": f"팔로워 {int(followers):,}명으로 영향력이 큽니다. 장기 브랜드 파트너십과 자체 상품 출시를 검토하세요."
        })

    # 추천이 너무 많으면 우선순위에 따라 제한
    recommendations.sort(key=lambda r: 0 if r["priority"] == "high" else 1 if r["priority"] == "medium" else 2)

    return recommendations[:5]  # 최대 5개까지만 반환


def generate_meta_ads_recommendations(campaign_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    메타 광고 캠페인 데이터를 분석하여 추천 생성

    Args:
        campaign_data: 캠페인 데이터 (spend, impressions, clicks, conversions 등)

    Returns:
        추천 리스트
    """
    recommendations = []

    spend = campaign_data.get("spend", 0)
    impressions = campaign_data.get("impressions", 0)
    clicks = campaign_data.get("clicks", 0)
    conversions = campaign_data.get("conversions", 0)

    # CTR (Click-Through Rate) 계산
    ctr = (clicks / impressions * 100) if impressions > 0 else 0

    # CVR (Conversion Rate) 계산
    cvr = (conversions / clicks * 100) if clicks > 0 else 0

    # CPC (Cost Per Click) 계산
    cpc = (spend / clicks) if clicks > 0 else 0

    # CPA (Cost Per Acquisition) 계산
    cpa = (spend / conversions) if conversions > 0 else 0

    # CTR 기반 추천
    if ctr > 2:
        recommendations.append({
            "type": "scale",
            "priority": "high",
            "action": "예산 증액 권장",
            "reason": f"CTR {ctr:.2f}%로 업계 평균(1.5%)을 초과합니다. 예산을 30-50% 증액하여 성과를 확대하세요."
        })
    elif ctr < 0.5:
        recommendations.append({
            "type": "creative",
            "priority": "high",
            "action": "광고 소재 교체",
            "reason": f"CTR {ctr:.2f}%로 매우 낮습니다. 이미지, 헤드라인, 설명을 A/B 테스트하여 개선하세요."
        })

    # CVR 기반 추천
    if cvr > 5:
        recommendations.append({
            "type": "scale",
            "priority": "high",
            "action": "성공 캠페인 확대",
            "reason": f"전환율 {cvr:.2f}%로 우수합니다. 유사 타깃으로 새 캠페인을 생성하세요."
        })
    elif cvr < 1 and clicks > 100:
        recommendations.append({
            "type": "landing",
            "priority": "high",
            "action": "랜딩 페이지 최적화",
            "reason": f"클릭은 {clicks}개지만 전환율 {cvr:.2f}%로 낮습니다. 랜딩 페이지의 UX와 CTA를 개선하세요."
        })

    # 비용 효율성 추천
    if cpa > 0 and cpa < 50:  # 목표 CPA가 50달러 미만이라고 가정
        recommendations.append({
            "type": "optimize",
            "priority": "medium",
            "action": "효율적인 캠페인 유지",
            "reason": f"고객 획득 비용(CPA) ₩{int(cpa):,}로 효율적입니다. 현재 전략을 유지하세요."
        })
    elif cpa > 100:
        recommendations.append({
            "type": "pause",
            "priority": "high",
            "action": "비효율 캠페인 중단",
            "reason": f"CPA ₩{int(cpa):,}로 너무 높습니다. 캠페인을 일시 중지하고 타깃과 소재를 전면 재검토하세요."
        })

    # 예산 소진 속도 추천
    if spend > 10000:  # 일일 예산이 10,000원 이상 소진되었다면
        recommendations.append({
            "type": "budget",
            "priority": "medium",
            "action": "예산 소진 모니터링",
            "reason": f"현재까지 ₩{int(spend):,} 소진되었습니다. 예산 소진 속도를 확인하고 필요 시 조정하세요."
        })

    recommendations.sort(key=lambda r: 0 if r["priority"] == "high" else 1 if r["priority"] == "medium" else 2)

    return recommendations[:5]
