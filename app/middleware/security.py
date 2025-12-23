"""Security middleware module."""

import secrets
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import Response


class CSRFMiddleware:
    """CSRF protection middleware."""

    def __init__(self):
        self._csrf_token_name = "X-CSRF-Token"
        self._csrf_cookie_name = "csrf_token"

    async def __call__(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" not in content_type:
                await self._validate_csrf_token(request)

        response = await call_next(request)

        if request.method == "GET":
            self._set_csrf_cookie(response)

        return response

    def _set_csrf_cookie(self, response: Response):
        """Set CSRF token cookie.

        Uses Double Submit Cookie pattern:
        - httponly=False: JavaScript must read cookie to include in form/header
        - secure=True: Cookie only sent over HTTPS
        - samesite=strict: Prevents CSRF from cross-site requests
        """
        csrf_token = secrets.token_urlsafe(32)
        response.set_cookie(
            self._csrf_cookie_name,
            csrf_token,
            httponly=False,  # Required for Double Submit Cookie pattern
            secure=True,
            samesite="strict",
            max_age=3600,
        )

    async def _validate_csrf_token(self, request: Request):
        """Validate CSRF token."""
        csrf_cookie = request.cookies.get(self._csrf_cookie_name)

        csrf_header = request.headers.get(self._csrf_token_name)
        csrf_form = None

        if request.headers.get("content-type", "").startswith(
            "application/x-www-form-urlencoded"
        ):
            form = await request.form()
            csrf_form = form.get("csrf_token")

        csrf_token = csrf_header or csrf_form

        if not csrf_cookie or not csrf_token or csrf_cookie != csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token"
            )


class RateLimitMiddleware:
    """API rate limiting middleware with memory cleanup."""

    def __init__(self, requests_per_minute: int = 60, max_entries: int = 10000):
        self.requests_per_minute = requests_per_minute
        self.max_entries = max_entries
        self.request_counts = {}
        self._last_cleanup_minute = 0

    def _cleanup_old_entries(self, current_minute: int):
        """오래된 항목 정리 - 메모리 누수 방지"""
        # 1분마다 정리 실행
        if current_minute <= self._last_cleanup_minute:
            return

        self._last_cleanup_minute = current_minute

        # 현재 분이 아닌 항목들 제거
        keys_to_remove = [
            key for key, data in self.request_counts.items()
            if data["minute"] != current_minute
        ]
        for key in keys_to_remove:
            del self.request_counts[key]

        # 최대 항목 수 초과 시 가장 오래된 것부터 제거
        if len(self.request_counts) > self.max_entries:
            sorted_keys = sorted(
                self.request_counts.keys(),
                key=lambda k: self.request_counts[k]["count"]
            )
            for key in sorted_keys[:len(self.request_counts) - self.max_entries]:
                del self.request_counts[key]

    async def __call__(self, request: Request, call_next):
        import time
        client_ip = request.client.host if request.client else "unknown"
        user_id = "anonymous"

        token = request.cookies.get("session")
        if token:
            try:
                from ..auth import auth_manager

                email = auth_manager.decode_token(token)
                user_id = email.split("@")[0]
            except Exception:
                pass

        client_key = f"{client_ip}:{user_id}"
        current_minute = int(time.time() / 60)

        # 주기적으로 오래된 항목 정리
        self._cleanup_old_entries(current_minute)

        if client_key not in self.request_counts:
            self.request_counts[client_key] = {"minute": current_minute, "count": 1}
        else:
            if self.request_counts[client_key]["minute"] != current_minute:
                self.request_counts[client_key] = {"minute": current_minute, "count": 1}
            else:
                self.request_counts[client_key]["count"] += 1

                if self.request_counts[client_key]["count"] > self.requests_per_minute:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again later.",
                        headers={"Retry-After": "60"},
                    )

        response = await call_next(request)

        remaining = (
            self.requests_per_minute - self.request_counts[client_key]["count"]
        )
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str((current_minute + 1) * 60)

        return response


class SecurityHeadersMiddleware:
    """Security headers middleware."""

    async def __call__(self, request: Request, call_next):
        response = await call_next(request)

        # CSP: 프로덕션에서는 unsafe-inline 제거 권장
        # 현재는 인라인 스크립트/스타일 사용으로 인해 unsafe-inline 허용
        # TODO: nonce 기반 CSP로 전환 시 unsafe-inline 제거
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response
