from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import select

from ..auth import auth_manager
from ..database import get_session
from ..models import ActivityLog, Subscription, SubscriptionTier, User, UserRole
from ..services.localization import translator

router = APIRouter()


@router.get("/login")
def login_page(request: Request, locale: str = "ko"):
    active_locale = getattr(request.state, "locale", locale)
    strings = translator.load_locale(active_locale)
    error_key = request.query_params.get("error")
    error_message = None
    if error_key:
        error_message = strings["auth"].get("errors", {}).get(error_key)
    return request.app.state.templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "locale": active_locale,
            "t": strings,
            "error": error_message,
        },
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session=Depends(get_session),
):
    user = session.exec(select(User).where(User.email == email)).first()
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)

    if not user or not auth_manager.verify_password(password, user.hashed_password):
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "locale": locale,
                "t": strings,
                "error": strings["auth"]["errors"]["invalid_credentials"],
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    token = auth_manager.create_access_token(user.email)
    redirect_to = "/dashboard" if user.role != UserRole.SUPER_ADMIN else "/super-admin"
    redirect_response = RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(redirect_response, token)

    session.add(ActivityLog(user_id=user.id, action="login"))
    session.commit()
    return redirect_response


@router.get("/signup")
def signup_page(request: Request, locale: str = "ko"):
    strings = translator.load_locale(locale)
    return request.app.state.templates.TemplateResponse(
        "signup.html",
        {"request": request, "locale": locale, "t": strings},
    )


@router.post("/signup")
def signup(
    email: EmailStr = Form(...),
    password: str = Form(...),
    role: UserRole = Form(UserRole.CREATOR),
    locale: str = Form("ko"),
    organization: str | None = Form(None),
    session=Depends(get_session),
):
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = auth_manager.hash_password(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        locale=locale,
        organization=organization,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE, max_accounts=1)
    session.add(subscription)
    session.add(ActivityLog(user_id=user.id, action="signup"))
    session.commit()
    return {"message": "Account created", "email": user.email}


@router.post("/logout")
def logout(response: Response):
    auth_manager.clear_login_cookie(response)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
