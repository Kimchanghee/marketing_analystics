"""
Security headers and CORS middleware for the application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict Transport Security (HTTPS only)
        # Only enable in production with HTTPS
        if request.url.hostname not in ["localhost", "127.0.0.1"]:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://www.google-analytics.com; "
            "frame-ancestors 'none';"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return response


def add_security_middleware(
    app: FastAPI,
    allowed_origins: list[str] = None,
    allowed_hosts: list[str] = None,
    environment: str = "development"
):
    """
    Add security middleware to the FastAPI app.

    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed CORS origins. If None, uses environment-based defaults.
        allowed_hosts: List of allowed hosts for TrustedHostMiddleware.
        environment: "production" or "development"
    """
    import os

    # 환경 변수에서 설정 가져오기
    env = environment or os.getenv("ENVIRONMENT", "development")
    is_production = env.lower() == "production"

    # 프로덕션/개발 환경에 따른 CORS 설정
    if allowed_origins is None:
        if is_production:
            # 프로덕션: 실제 도메인만 허용
            prod_domain = os.getenv("ALLOWED_ORIGIN", "https://creatorcontrolcenter.com")
            allowed_origins = [prod_domain]
        else:
            # 개발: localhost 허용
            allowed_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
            ]

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "X-Total-Count"],
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Trusted host middleware (prevents host header attacks)
    # 프로덕션 환경에서만 활성화
    if is_production:
        if allowed_hosts is None:
            prod_host = os.getenv("ALLOWED_HOST", "creatorcontrolcenter.com")
            allowed_hosts = [prod_host, f"*.{prod_host}"]

        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
