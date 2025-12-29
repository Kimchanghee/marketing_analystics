import logging
import os
import sys
import time
from pathlib import Path

# 로깅 설정 - 환경 변수로 레벨 조정 가능
# LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (기본값: WARNING)
_log_level_name = os.getenv("LOG_LEVEL", "WARNING").upper()
_log_level = getattr(logging, _log_level_name, logging.WARNING)

logging.basicConfig(
    level=_log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .config import get_settings

from .auth import auth_manager
from .database import get_session, session_context
from .dependencies import get_current_user
from .models import SocialAccount, User

from .routers import admin, ai_pd, channels, dashboard, subscriptions
from .routers.auth import router as auth_router

from .services.localization import translator
from .services.social.social_auth import social_auth_service

from .seo import get_seo_service, get_sitemap_generator, generate_robots_txt
from .middleware.security_headers import add_security_middleware

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR.parent / "ui"

app = FastAPI(title="Creator Control Center")
app.state.asset_version = os.getenv("ASSET_VERSION", str(int(time.time())))

# Add security middleware (CORS, security headers, trusted hosts)
settings = get_settings()
add_security_middleware(app, environment=settings.environment)


def build_asset_url(request, path: str) -> str:
    """Return cache-busted asset URL for static files.

    In production, forces HTTPS. In development, preserves the original scheme.
    """
    version = "1"
    if request is not None:
        url = str(request.url_for("static", path=path))
        version = getattr(request.app.state, "asset_version", "1")
    else:
        url = f"/static/{path}"
        version = getattr(app.state, "asset_version", "1")

    settings = get_settings()
    if settings.is_production and url.startswith("http://"):
        url = "https://" + url[len("http://"):]

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}v={version}"
app.mount("/static", StaticFiles(directory=UI_DIR / "static"), name="static")

# 템플릿 디렉토리 설정 (호환성을 위해 여러 경로 지원)
template_dirs = [
    str(UI_DIR),  # 루트 (components, layouts, pages 접근)
    str(UI_DIR / "templates"),  # 레거시 templates 폴더 (호환성)
]
app.state.templates = Jinja2Templates(directory=template_dirs)
app.state.templates.env.globals["asset_url"] = build_asset_url


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러 - 예외 타입별 세분화된 처리"""
    from fastapi import HTTPException
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
    from pydantic import ValidationError

    # 사용자 정보 추출 (가능한 경우)
    user_info = "anonymous"
    try:
        token = request.cookies.get("session")
        if token:
            email = auth_manager.decode_token(token)
            user_info = email
    except Exception:
        pass

    # 클라이언트 IP 추출
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not client_ip and request.client:
        client_ip = request.client.host

    # 예외 타입별 처리
    if isinstance(exc, HTTPException):
        # HTTPException은 이미 적절히 처리되므로 로깅만
        logger.warning(
            f"HTTPException: status={exc.status_code} detail={exc.detail} "
            f"path={request.url.path} user={user_info} ip={client_ip}"
        )
        raise exc

    if isinstance(exc, ValidationError):
        logger.warning(
            f"ValidationError: {exc.error_count()} errors "
            f"path={request.url.path} user={user_info} ip={client_ip}"
        )
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": exc.errors()}
        )

    if isinstance(exc, OperationalError):
        logger.critical(
            f"Database connection error: {exc} "
            f"path={request.url.path} user={user_info} ip={client_ip}",
            exc_info=True
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "Database connection error. Please try again later."}
        )

    if isinstance(exc, IntegrityError):
        logger.error(
            f"Database integrity error: {exc} "
            f"path={request.url.path} user={user_info} ip={client_ip}",
            exc_info=True
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "Data conflict occurred."}
        )

    if isinstance(exc, SQLAlchemyError):
        logger.error(
            f"Database error: {type(exc).__name__}: {exc} "
            f"path={request.url.path} user={user_info} ip={client_ip}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error occurred."}
        )

    if isinstance(exc, (ValueError, KeyError, TypeError)):
        logger.error(
            f"Application error: {type(exc).__name__}: {exc} "
            f"path={request.url.path} user={user_info} ip={client_ip}",
            exc_info=True
        )
        settings = get_settings()
        if settings.is_production:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request."}
            )
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "type": type(exc).__name__}
        )

    # 알 수 없는 예외 - 가장 상세하게 로깅
    logger.critical(
        f"Unhandled exception: {type(exc).__name__}: {exc} "
        f"path={request.url.path} method={request.method} user={user_info} ip={client_ip}",
        exc_info=True
    )

    # 프로덕션에서는 내부 정보 노출 방지
    settings = get_settings()
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal error occurred. Please try again later."
            }
        )

    # 개발 환경에서는 디버깅을 위해 상세 정보 제공
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred.",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


@app.on_event("startup")
async def on_startup() -> None:
    import os
    import asyncio
    from .cache import cache

    logger.info("=" * 50)
    logger.info("Application startup beginning")
    logger.info(f"PORT environment variable: {os.getenv('PORT', 'not set')}")
    logger.info(f"DATABASE_URL configured: {'postgresql' in (os.getenv('DATABASE_URL', '') or '')}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'not set')}")
    logger.info("=" * 50)
    logger.info("Application startup completed - database will initialize on first request")

    # 캐시 정리 스케줄러 (10분마다)
    async def cleanup_cache_periodically():
        while True:
            await asyncio.sleep(600)  # 10분
            cache.cleanup_expired()

    asyncio.create_task(cleanup_cache_periodically())


@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """요청 시간 모니터링 미들웨어"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    # 응답 헤더에 처리 시간 추가
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"

    # 느린 요청만 로깅 (1초 이상)
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}s"
        )

    return response


@app.middleware("http")
async def localization_middleware(request: Request, call_next):
    locale = request.query_params.get("lang") or "ko"
    token = request.cookies.get("session")
    if token:
        try:
            email = auth_manager.decode_token(token)
            with session_context() as session:
                user = session.exec(select(User).where(User.email == email)).first()
                if user:
                    locale = user.locale
        except Exception as e:
            # Invalid or expired token - expected, just use default locale
            logger.debug(f"Could not get user locale from token: {e}")
    request.state.locale = locale
    response = await call_next(request)
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run with database connection check"""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "environment": "unknown"
    }

    # 환경 확인
    try:
        from .config import get_settings
        settings = get_settings()
        health_status["environment"] = settings.environment
        health_status["database_configured"] = bool(settings.database_url and "postgresql" in settings.database_url)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        health_status["config_error"] = str(e)

    # 데이터베이스 연결 확인
    try:
        from .database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "disconnected"
        health_status["database_error"] = str(e)
        health_status["status"] = "unhealthy"

    return health_status


@app.get("/")
async def landing(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)

    login_error_key = request.query_params.get("login_error")
    signup_error_key = request.query_params.get("signup_error")
    signup_success_key = request.query_params.get("signup_success")
    return app.state.templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "seo": seo_service,
            "page": "home",
            "login_error": strings["auth"].get(login_error_key) if login_error_key else None,
            "signup_error": strings["auth"].get(signup_error_key) if signup_error_key else None,
            "signup_success": strings["auth"].get(signup_success_key) if signup_success_key else None,
        },
    )


@app.get("/services")
async def services(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "services.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "services"},
    )


@app.get("/personal")
async def personal_plan(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "personal.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "personal"},
    )


@app.get("/business")
async def business_plan(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "business.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "business"},
    )


@app.get("/pricing", include_in_schema=False)
async def pricing_redirect(request: Request):
    target = request.query_params.get("type", "personal").lower()
    if target == "business":
        return RedirectResponse(url="/business", status_code=307)
    return RedirectResponse(url="/personal", status_code=307)


@app.get("/support")
async def support(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "support.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "support"},
    )


@app.get("/terms")
async def terms_of_service(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "terms.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "terms"},
    )


@app.get("/privacy")
async def privacy_policy(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "privacy.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "privacy"},
    )


@app.get("/contact")
async def contact_page(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)
    return app.state.templates.TemplateResponse(
        "contact.html",
        {"request": request, "locale": locale, "t": strings, "seo": seo_service, "page": "contact"},
    )


@app.post("/contact")
async def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    seo_service = get_seo_service(locale)

    # Send contact email via Resend if configured
    from .services.email.resend_email import resend_email_service

    settings = get_settings()
    success_message = False
    error_message = False

    if settings.use_resend:
        result = resend_email_service.send_admin_notification(
            to=settings.resend_from_email,
            subject_text=f"[Contact] {subject}",
            message=f"From: {name} <{email}>\n\nMessage:\n{message}",
        )
        if result.success:
            success_message = True
        else:
            error_message = True
    else:
        # Log the contact request if Resend is not configured
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Contact form submission: {name} <{email}> - {subject}")
        success_message = True

    return app.state.templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "seo": seo_service,
            "page": "contact",
            "success_message": success_message,
            "error_message": error_message,
        },
    )


@app.get("/profile")
async def profile(
    request: Request,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    db_user = session.exec(select(User).where(User.id == user.id)).first() or user
    social_accounts = session.exec(
        select(SocialAccount).where(SocialAccount.user_id == db_user.id)
    ).all()
    locale = db_user.locale
    strings = translator.load_locale(locale)
    social_status = request.query_params.get("social")
    credentials_status = request.query_params.get("credentials")
    credentials_error_key = request.query_params.get("credentials_error")
    code_status = request.query_params.get("code")
    social_error_key = request.query_params.get("social_error")
    context = {
        "request": request,
        "user": db_user,
        "t": strings,
        "locale": locale,
        "providers": list(social_auth_service.get_supported_providers()),
        "social_success": strings["auth"].get("social_linked") if social_status == "linked" else None,
        "credentials_success": strings["auth"].get("password_updated") if credentials_status == "updated" else None,
        "credentials_error": strings["auth"].get(credentials_error_key) if credentials_error_key else None,
        "code_status": strings["auth"].get("verification_sent") if code_status == "sent" else None,
        "social_error": strings["auth"].get(social_error_key) if social_error_key else None,
        "social_accounts": social_accounts,
    }
    return app.state.templates.TemplateResponse("profile.html", context)


@app.get("/sitemap.xml")
async def sitemap():
    """동적 sitemap.xml 생성"""
    sitemap_gen = get_sitemap_generator()
    xml_content = sitemap_gen.generate_sitemap()
    return Response(content=xml_content, media_type="application/xml")


@app.get("/robots.txt")
async def robots():
    """robots.txt 제공"""
    robots_content = generate_robots_txt()
    return Response(content=robots_content, media_type="text/plain")


app.include_router(auth_router)
app.include_router(dashboard.router)
app.include_router(channels.router)
app.include_router(admin.router)
app.include_router(subscriptions.router)
app.include_router(ai_pd.router)
