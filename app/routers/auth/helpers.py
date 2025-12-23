"""
인증 라우터 공통 헬퍼 함수

모든 인증 관련 라우터에서 공유하는 유틸리티 함수들
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi import status

from ...models import UserRole
from ...services.localization import translator


def determine_locale(request: Request) -> str:
    """요청에서 로케일 결정"""
    return getattr(request.state, "locale", request.query_params.get("lang", "ko"))


def template_context(
    request: Request, locale: str, strings: dict, extra: dict | None = None
) -> dict:
    """템플릿 컨텍스트 생성"""
    context = {"request": request, "locale": locale, "t": strings}
    if extra:
        context.update(extra)
    return context


def append_query_params(url: str, params: dict[str, str | None]) -> str:
    """URL에 쿼리 파라미터 추가"""
    filtered = {k: v for k, v in params.items() if v}
    if not filtered:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(filtered)}"


def resolve_role(value: str | None) -> UserRole:
    """문자열에서 UserRole 결정"""
    if not value:
        return UserRole.CREATOR
    try:
        return UserRole(value)
    except ValueError:
        return UserRole.CREATOR


def social_error_redirect(origin: str | None, locale: str, error_key: str) -> RedirectResponse:
    """소셜 인증 오류 리다이렉트"""
    target = origin or "/login"
    redirect_url = append_query_params(target, {"lang": locale, "social_error": error_key})
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("oauth_state")
    return response


def get_client_ip(request: Request) -> str:
    """클라이언트 IP 주소 추출 (프록시 헤더 처리)"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_safe_redirect_url(url: str | None) -> bool:
    """리다이렉트 URL 안전성 검증 (Open Redirect 방지)

    허용:
    - None/empty (기본값 사용)
    - / 로 시작하는 상대 경로
    - 프로토콜이나 도메인 없음
    """
    if not url:
        return True

    # / 로 시작해야 함
    if not url.startswith("/"):
        return False

    # 프로토콜 상대 URL 차단 (//example.com)
    if url.startswith("//"):
        return False

    # 프로토콜 포함 URL 차단
    if "://" in url:
        return False

    # JavaScript URL 차단
    if url.lower().startswith("javascript:"):
        return False

    return True
