"""
관리자 라우터 공통 헬퍼 함수

모든 관리자 관련 라우터에서 공유하는 유틸리티 함수들
"""

import os

from fastapi import Request

from ...services.localization import translator

# 테스트 이메일 수신자 - 환경변수에서 가져오거나 관리자 이메일 사용
TEST_EMAIL_RECIPIENT = os.getenv("TEST_EMAIL_RECIPIENT", "admin@creatorcontrolcenter.com")


def get_admin_context(request: Request, user, session) -> dict:
    """관리자 페이지용 기본 컨텍스트 생성"""
    locale = user.locale
    strings = translator.load_locale(locale)

    return {
        "request": request,
        "user": user,
        "locale": locale,
        "t": strings,
    }
