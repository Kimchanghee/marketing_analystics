from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .auth import auth_manager
from .database import get_session, init_db
from .dependencies import get_current_user
from .models import SocialAccount, User
from .routers import admin, auth, dashboard, subscriptions
from .services.localization import translator
from .services.social_auth import social_auth_service

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Creator Control Center")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.middleware("http")
async def localization_middleware(request: Request, call_next):
    locale = request.query_params.get("lang") or "ko"
    token = request.cookies.get("session")
    if token:
        try:
            email = auth_manager.decode_token(token)
            with get_session() as session:
                user = session.exec(select(User).where(User.email == email)).first()
                if user:
                    locale = user.locale
        except Exception:  # noqa: BLE001
            pass
    request.state.locale = locale
    response = await call_next(request)
    return response


@app.get("/")
async def landing(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    login_error_key = request.query_params.get("login_error")
    signup_error_key = request.query_params.get("signup_error")
    signup_success_key = request.query_params.get("signup_success")
    return app.state.templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "login_error": strings["auth"].get(login_error_key) if login_error_key else None,
            "signup_error": strings["auth"].get(signup_error_key) if signup_error_key else None,
            "signup_success": strings["auth"].get(signup_success_key) if signup_success_key else None,
        },
    )


@app.get("/services")
async def services(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    return app.state.templates.TemplateResponse(
        "services.html",
        {"request": request, "locale": locale, "t": strings},
    )


@app.get("/personal")
async def personal_plan(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    return app.state.templates.TemplateResponse(
        "personal.html",
        {"request": request, "locale": locale, "t": strings},
    )


@app.get("/business")
async def business_plan(request: Request):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    return app.state.templates.TemplateResponse(
        "business.html",
        {"request": request, "locale": locale, "t": strings},
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
    return app.state.templates.TemplateResponse(
        "support.html",
        {"request": request, "locale": locale, "t": strings},
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


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(subscriptions.router)
