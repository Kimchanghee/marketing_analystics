from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from .auth import auth_manager
from .database import get_session, init_db
from .dependencies import get_current_user
from .models import User
from .routers import admin, auth, dashboard, subscriptions
from .services.localization import translator

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
    return app.state.templates.TemplateResponse(
        "landing.html",
        {"request": request, "locale": locale, "t": strings},
    )


@app.get("/profile")
async def profile(request: Request, user: User = Depends(get_current_user)):
    locale = user.locale
    strings = translator.load_locale(locale)
    return app.state.templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "t": strings, "locale": locale},
    )


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(subscriptions.router)
