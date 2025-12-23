"""
관리자 라우터 모듈

이 패키지는 모든 관리자 관련 라우트를 포함합니다:
- super_admin: 슈퍼 관리자 대시보드
- email: 관리자 이메일 관리
- users: 사용자 관리
- payments: 결제 관리
- inquiries: 문의 관리
- ai_settings: AI 설정 관리
"""

from fastapi import APIRouter

from .super_admin import router as super_admin_router
from .email import router as email_router
from .users import router as users_router
from .payments import router as payments_router
from .inquiries import router as inquiries_router
from .ai_settings import router as ai_settings_router

router = APIRouter()

# 모든 하위 라우터 포함
router.include_router(super_admin_router, tags=["admin-dashboard"])
router.include_router(email_router, tags=["admin-email"])
router.include_router(users_router, tags=["admin-users"])
router.include_router(payments_router, tags=["admin-payments"])
router.include_router(inquiries_router, tags=["admin-inquiries"])
router.include_router(ai_settings_router, tags=["admin-ai"])

__all__ = ["router"]
