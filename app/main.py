import logging
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .auth import auth_manager
from .database import get_session, init_db, session_context
from .dependencies import get_current_user
from .models import SocialAccount, User
from .routers import admin, ai_pd, auth, channels, dashboard, subscriptions
from .services.localization import translator
from .services.social_auth import social_auth_service
from .seo import get_seo_service, get_sitemap_generator, generate_robots_txt

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Creator Control Center")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러 - 모든 에러를 로깅"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")

    # 사용자에게 친절한 에러 메시지 반환
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred. Please check the logs for more details.",
            "error": str(exc)
        }
    )


@app.on_event("startup")
def on_startup() -> None:
    try:
        logger.info("Starting database initialization...")
        init_db()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        # Log the error but don't prevent the app from starting
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        logger.warning("Application will start but database operations may fail")


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
        except Exception:  # noqa: BLE001
            pass
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


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(channels.router)
app.include_router(admin.router)
app.include_router(subscriptions.router)
app.include_router(ai_pd.router)
