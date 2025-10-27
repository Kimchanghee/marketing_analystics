"""AI PD (Personal Development) Service using Google Gemini API

This service provides AI-powered analysis and feedback for creators and managers.
It analyzes all channel data, posts, and performance metrics to provide personalized insights.
"""
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from sqlmodel import Session, select

from ..config import get_settings
from ..models import (
    ChannelAccount,
    CreatorInquiry,
    ManagerAPIKey,
    User,
    UserRole,
)


class AIPDService:
    """AI Personal Development service for creators and managers"""

    def __init__(self):
        self.settings = get_settings()
        self._configure_api()

    def _configure_api(self):
        """Configure Gemini API with key from settings"""
        if self.settings.gemini_api_key:
            genai.configure(api_key=self.settings.gemini_api_key)

    def _get_manager_api_key(self, session: Session, manager_id: int) -> Optional[str]:
        """Get manager's encrypted Gemini API key"""
        api_key_record = session.exec(
            select(ManagerAPIKey).where(ManagerAPIKey.manager_id == manager_id)
        ).first()

        if api_key_record:
            return api_key_record.api_key
        return None

    def _generate_creator_context(
        self,
        user: User,
        channels: List[ChannelAccount],
        snapshots: Dict[int, Dict[str, Any]]
    ) -> str:
        """Generate context about a creator's channels and performance"""
        context_parts = [
            f"크리에이터 정보:",
            f"- 이름: {user.name or user.email}",
            f"- 이메일: {user.email}",
            f"- 조직: {user.organization or '개인'}",
            f"\n연결된 채널 ({len(channels)}개):"
        ]

        for channel in channels:
            snapshot = snapshots.get(channel.id, {})
            context_parts.append(f"\n### {channel.platform} - @{channel.account_name}")
            context_parts.append(f"- 구독자/팔로워: {snapshot.get('followers', 0):,}명")
            context_parts.append(f"- 성장률: {snapshot.get('growth_rate', 0)}%")
            context_parts.append(f"- 참여율: {snapshot.get('engagement_rate', 0)}%")

            recent_posts = snapshot.get('recent_posts', [])
            if recent_posts:
                context_parts.append(f"\n최근 게시물 ({len(recent_posts)}개):")
                for i, post in enumerate(recent_posts[:5], 1):
                    context_parts.append(
                        f"{i}. {post.get('title', 'N/A')[:50]} "
                        f"(좋아요: {post.get('likes', 0):,}, "
                        f"댓글: {post.get('comments', 0):,}, "
                        f"조회수: {post.get('impressions', 0):,})"
                    )

        return "\n".join(context_parts)

    def _generate_manager_context(
        self,
        manager: User,
        creators: List[User],
        all_channels: Dict[int, List[ChannelAccount]],
        all_snapshots: Dict[int, Dict[int, Dict[str, Any]]]
    ) -> str:
        """Generate context about all managed creators"""
        context_parts = [
            f"기업 관리자 정보:",
            f"- 이름: {manager.name or manager.email}",
            f"- 조직: {manager.organization or 'N/A'}",
            f"\n관리 중인 크리에이터 ({len(creators)}명):"
        ]

        for creator in creators:
            channels = all_channels.get(creator.id, [])
            snapshots = all_snapshots.get(creator.id, {})

            context_parts.append(f"\n## {creator.name or creator.email}")
            context_parts.append(f"총 {len(channels)}개 채널:")

            for channel in channels:
                snapshot = snapshots.get(channel.id, {})
                context_parts.append(
                    f"- {channel.platform}(@{channel.account_name}): "
                    f"{snapshot.get('followers', 0):,}명 구독자, "
                    f"성장률 {snapshot.get('growth_rate', 0)}%, "
                    f"참여율 {snapshot.get('engagement_rate', 0)}%"
                )

        return "\n".join(context_parts)

    def analyze_creator_performance(
        self,
        user: User,
        channels: List[ChannelAccount],
        snapshots: Dict[int, Dict[str, Any]],
        question: str,
        api_key: Optional[str] = None
    ) -> str:
        """Analyze creator performance and answer questions using Gemini AI"""
        # Use provided API key or default from settings
        if api_key:
            genai.configure(api_key=api_key)
        elif not self.settings.gemini_api_key:
            return "AI 분석 서비스를 사용하려면 Gemini API 키가 필요합니다."

        try:
            # Generate context
            context = self._generate_creator_context(user, channels, snapshots)

            # Create prompt
            prompt = f"""당신은 크리에이터의 소셜 미디어 성과를 분석하는 전문 AI PD(Personal Development) 컨설턴트입니다.

{context}

크리에이터의 질문: {question}

위의 데이터를 바탕으로 구체적이고 실행 가능한 피드백을 제공해주세요. 다음 사항을 포함하세요:
1. 현재 성과 평가
2. 강점과 개선점
3. 구체적인 액션 아이템 (3-5개)
4. 예상되는 효과

답변은 친절하고 격려적인 톤으로 작성해주세요."""

            # Generate response
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)

            return response.text

        except Exception as e:
            return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_manager_portfolio(
        self,
        session: Session,
        manager: User,
        creators: List[User],
        all_channels: Dict[int, List[ChannelAccount]],
        all_snapshots: Dict[int, Dict[int, Dict[str, Any]]],
        question: str
    ) -> str:
        """Analyze manager's entire creator portfolio using Gemini AI"""
        # Get manager's API key
        api_key = self._get_manager_api_key(session, manager.id)

        if not api_key and not self.settings.gemini_api_key:
            return "AI 분석 서비스를 사용하려면 Gemini API 키를 등록해주세요."

        if api_key:
            genai.configure(api_key=api_key)

        try:
            # Generate context
            context = self._generate_manager_context(
                manager, creators, all_channels, all_snapshots
            )

            # Create prompt
            prompt = f"""당신은 크리에이터 매니지먼트 전문 AI PD 컨설턴트입니다.

{context}

매니저의 질문: {question}

위의 데이터를 바탕으로 전문적이고 실행 가능한 인사이트를 제공해주세요. 다음 사항을 포함하세요:
1. 전체 포트폴리오 현황 분석
2. 주목할 만한 성과와 우려 사항
3. 크리에이터별 맞춤 전략 제안
4. 포트폴리오 최적화 방안
5. 구체적인 다음 액션 아이템

답변은 전문적이면서도 실용적인 톤으로 작성해주세요."""

            # Generate response
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)

            return response.text

        except Exception as e:
            return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

    def generate_inquiry_response(
        self,
        session: Session,
        inquiry: CreatorInquiry,
        context_data: Dict[str, Any]
    ) -> str:
        """Generate AI draft response for creator inquiry"""
        # Get manager's API key
        api_key = self._get_manager_api_key(session, inquiry.manager_id)

        if not api_key and not self.settings.gemini_api_key:
            return "AI 답변 생성을 위해서는 Gemini API 키가 필요합니다."

        if api_key:
            genai.configure(api_key=api_key)

        try:
            # Create prompt
            prompt = f"""당신은 크리에이터 지원 전문 CS AI입니다.

문의 카테고리: {inquiry.category.value}
문의 제목: {inquiry.subject}
문의 내용:
{inquiry.message}

추가 컨텍스트:
{context_data}

위 문의에 대한 전문적이고 도움이 되는 답변 초안을 작성해주세요. 다음 사항을 포함하세요:
1. 문의 내용에 대한 이해 확인
2. 구체적인 해결 방법 또는 안내
3. 추가로 필요한 정보가 있다면 명시
4. 친절하고 격려적인 마무리

답변은 한국어로 작성하고, 전문적이면서도 따뜻한 톤을 유지해주세요."""

            # Generate response
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)

            return response.text

        except Exception as e:
            return f"AI 답변 생성 중 오류가 발생했습니다: {str(e)}"

    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt used for AI PD service (for super admin view)"""
        return """AI PD (Personal Development) 서비스 시스템 프롬프트:

당신은 크리에이터와 매니저를 위한 전문 AI 컨설턴트입니다.

핵심 역할:
1. 크리에이터 개인: 소셜 미디어 성과 분석, 콘텐츠 전략 제안, 성장 방안 제시
2. 비즈니스 매니저: 포트폴리오 분석, 크리에이터별 맞춤 전략, 전체 최적화 방안

답변 원칙:
- 데이터 기반의 구체적인 인사이트 제공
- 실행 가능한 액션 아이템 포함
- 긍정적이고 격려적인 톤 유지
- 전문성과 따뜻함의 균형

제한사항:
- 개인정보 보호 최우선
- 과도한 약속 지양
- 불확실한 정보는 명시
- 윤리적 가이드라인 준수"""


# Global instance
ai_pd_service = AIPDService()
