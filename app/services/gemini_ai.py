"""Gemini AI 통합 서비스"""
import json
import logging
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Base exception for Gemini AI service errors"""
    pass


class AIGenerationError(GeminiServiceError):
    """Raised when AI content generation fails"""
    pass


class GeminiAIService:
    """Gemini 2.0 Flash를 사용한 AI 서비스"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Gemini API 키
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai 라이브러리가 설치되지 않았습니다. "
                "pip install google-generativeai를 실행하세요."
            )

        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_cs_response(
        self,
        inquiry_subject: str,
        inquiry_message: str,
        inquiry_category: str,
        creator_info: dict,
        context_data: Optional[dict] = None
    ) -> str:
        """
        크리에이터 문의에 대한 CS 답변 초안 생성

        Args:
            inquiry_subject: 문의 제목
            inquiry_message: 문의 내용
            inquiry_category: 문의 카테고리
            creator_info: 크리에이터 정보 (이름, 이메일, 조직 등)
            context_data: 추가 컨텍스트 데이터 (채널 정보, 구독 정보 등)

        Returns:
            AI가 생성한 답변 초안

        Raises:
            AIGenerationError: If AI generation fails
        """
        # 컨텍스트 정보 준비
        context_str = ""
        if context_data:
            if "subscription" in context_data:
                context_str += f"\n구독 플랜: {context_data['subscription']}"
            if "channel_count" in context_data:
                context_str += f"\n연결된 채널 수: {context_data['channel_count']}"
            if "channels" in context_data:
                channels_info = ", ".join([
                    f"{ch['platform']}({ch['account_name']})"
                    for ch in context_data['channels'][:3]
                ])
                context_str += f"\n주요 채널: {channels_info}"

        # 프롬프트 구성
        prompt = f"""당신은 크리에이터 관리 플랫폼의 전문 고객 지원 담당자입니다.
다음 크리에이터의 문의에 대한 친절하고 전문적인 답변 초안을 작성해주세요.

[크리에이터 정보]
- 이름: {creator_info.get('name', '알 수 없음')}
- 이메일: {creator_info.get('email', '알 수 없음')}
- 조직: {creator_info.get('organization', '없음')}
{context_str}

[문의 카테고리]
{inquiry_category}

[문의 제목]
{inquiry_subject}

[문의 내용]
{inquiry_message}

[답변 작성 가이드라인]
1. 크리에이터를 존중하고 친절한 톤으로 작성
2. 문의 내용을 정확히 이해했음을 표현
3. 구체적이고 실행 가능한 해결책 제시
4. 필요시 단계별 안내 포함
5. 추가 도움이 필요하면 언제든 연락하라는 메시지 포함
6. 한국어로 작성
7. 200-400자 정도의 적절한 길이
8. 관리자가 검토하고 수정할 수 있는 초안임을 고려

답변 초안:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"AI CS response generation failed: {e}", exc_info=True)
            raise AIGenerationError(f"AI 답변 생성 중 오류가 발생했습니다: {str(e)}") from e

    def summarize_creator_activity(
        self,
        creator_info: dict,
        channels_data: list,
        recent_inquiries: list,
        time_period: str = "지난 7일"
    ) -> str:
        """
        크리에이터의 활동을 요약

        Args:
            creator_info: 크리에이터 정보
            channels_data: 채널 데이터 리스트
            recent_inquiries: 최근 문의 내역
            time_period: 요약 기간

        Returns:
            활동 요약 텍스트

        Raises:
            AIGenerationError: If AI generation fails
        """
        # 채널 요약
        channels_summary = []
        for channel in channels_data[:5]:  # 최대 5개
            channels_summary.append(
                f"- {channel.get('platform', '?')}: {channel.get('account_name', '?')} "
                f"(팔로워: {channel.get('followers', 0):,}명, "
                f"성장률: {channel.get('growth_rate', 0):.1f}%)"
            )

        # 문의 요약
        inquiries_summary = []
        for inq in recent_inquiries[:3]:  # 최대 3개
            inquiries_summary.append(
                f"- [{inq.get('category', '일반')}] {inq.get('subject', '제목 없음')}"
            )

        prompt = f"""다음 크리에이터의 {time_period} 활동을 간결하게 요약해주세요.

[크리에이터]
{creator_info.get('name', creator_info.get('email', '알 수 없음'))}

[채널 현황]
{chr(10).join(channels_summary) if channels_summary else '연결된 채널 없음'}

[최근 문의]
{chr(10).join(inquiries_summary) if inquiries_summary else '최근 문의 없음'}

100-150자 내외로 핵심만 요약해주세요. 주요 지표 변화, 문의 패턴, 주목할 사항을 중심으로 작성하세요."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Activity summary generation failed: {e}", exc_info=True)
            raise AIGenerationError(f"활동 요약 생성 중 오류가 발생했습니다: {str(e)}") from e

    def analyze_inquiry_category(self, subject: str, message: str) -> str:
        """
        문의 내용을 분석하여 적절한 카테고리를 추천

        Args:
            subject: 문의 제목
            message: 문의 내용

        Returns:
            추천 카테고리 (technical, account, billing, feature_request, bug_report, general 중 하나)

        Raises:
            AIGenerationError: If AI generation fails
        """
        prompt = f"""다음 고객 문의를 분석하여 가장 적절한 카테고리를 하나만 선택해주세요.

제목: {subject}
내용: {message}

카테고리 옵션:
- technical: 기술적 문제나 사용법 문의
- account: 계정 관련 문의 (로그인, 권한, 설정 등)
- billing: 결제, 구독, 환불 관련
- feature_request: 새로운 기능 요청이나 개선 제안
- bug_report: 버그나 오류 신고
- general: 위 카테고리에 해당하지 않는 일반 문의

답변: (카테고리 이름만 영문으로 출력)"""

        try:
            response = self.model.generate_content(prompt)
            category = response.text.strip().lower()

            # 유효한 카테고리인지 확인
            valid_categories = ["technical", "account", "billing", "feature_request", "bug_report", "general"]
            if category in valid_categories:
                return category

            # AI가 유효하지 않은 카테고리를 반환한 경우 기본값 반환
            logger.warning(f"AI returned invalid category '{category}', using 'general' as fallback")
            return "general"
        except Exception as e:
            logger.error(f"Category analysis failed: {e}", exc_info=True)
            raise AIGenerationError(f"카테고리 분석 중 오류가 발생했습니다: {str(e)}") from e


def get_gemini_service(api_key: str) -> GeminiAIService:
    """
    Gemini AI 서비스 인스턴스 생성

    Args:
        api_key: Gemini API 키

    Returns:
        GeminiAIService 인스턴스
    """
    return GeminiAIService(api_key)
