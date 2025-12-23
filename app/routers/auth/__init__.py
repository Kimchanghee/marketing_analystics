"""
인증 라우터 모듈

이 패키지는 모든 인증 관련 라우트를 포함합니다:
- login: 로그인/로그아웃
- signup: 회원가입
- oauth: 소셜 로그인 (Google, Apple 등)
- recovery: 비밀번호/계정 복구
- credentials: 비밀번호 설정/변경
"""

from fastapi import APIRouter

from .login import router as login_router
from .signup import router as signup_router
from .oauth import router as oauth_router
from .recovery import router as recovery_router
from .credentials import router as credentials_router

router = APIRouter()

# 모든 하위 라우터 포함
router.include_router(login_router, tags=["auth-login"])
router.include_router(signup_router, tags=["auth-signup"])
router.include_router(oauth_router, tags=["auth-oauth"])
router.include_router(recovery_router, tags=["auth-recovery"])
router.include_router(credentials_router, tags=["auth-credentials"])

__all__ = ["router"]
