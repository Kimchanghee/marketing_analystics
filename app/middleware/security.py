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
        """Set CSRF token cookie."""
        csrf_token = secrets.token_urlsafe(32)
        response.set_cookie(
            self._csrf_cookie_name,
            csrf_token,
            httponly=False,
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
    """API rate limiting middleware."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}

    async def __call__(self, request: Request, call_next):
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
        current_minute = int(request.scope.get("time", 0) / 60)

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

        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            ),
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response
