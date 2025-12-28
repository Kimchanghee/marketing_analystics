"""
서비스 레이어 모듈

이 패키지는 비즈니스 로직을 담당하는 모든 서비스를 포함합니다.

서브모듈:
- email: 이메일 관련 서비스 (Gmail, Resend, 인증)
- ai: AI 관련 서비스 (Gemini, 추천, PD)
- social: 소셜 미디어 서비스 (OAuth, 채널 연동)

기타 서비스:
- account_recovery: 계정 복구
- login_throttle: 로그인 제한
- localization: 다국어 지원
- crypto: 암호화
- pdf_generator: PDF 생성
- config_status: 설정 상태 확인
"""

# 하위 모듈 import (호환성 유지)
from . import email
from . import ai
from . import social

# 기타 서비스 직접 import
from .account_recovery import account_recovery_service
from .login_throttle import login_throttle_service
from .localization import translator
from .crypto import encrypt, decrypt, DecryptionError
from .pdf_generator import generate_dashboard_pdf
from .config_status import get_config_status

__all__ = [
    # 서브모듈
    "email",
    "ai",
    "social",
    # 기타 서비스
    "account_recovery_service",
    "login_throttle_service",
    "translator",
    "encrypt",
    "decrypt",
    "DecryptionError",
    "generate_dashboard_pdf",
    "get_config_status",
]
