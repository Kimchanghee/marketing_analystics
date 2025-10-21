from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from sqlmodel import select

from ..auth import auth_manager
from ..database import get_session
from ..models import ActivityLog, Subscription, SubscriptionTier, User, UserRole
from ..services.localization import translator

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    locale = getattr(request.state, "locale", request.query_params.get("lang", "ko"))
    strings = translator.load_locale(locale)
    return request.app.state.templates.TemplateResponse(
        "login.html",
        {"request": request, "locale": locale, "t": strings},
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session=Depends(get_session),
):
    locale = getattr(request.state, "locale", "ko")
    strings = translator.load_locale(locale)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not auth_manager.verify_password(password, user.hashed_password):
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "locale": locale,
                "t": strings,
                "error": strings["auth"].get("invalid_credentials", "Invalid credentials"),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not user.is_active:
        return request.app.state.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "locale": locale,
                "t": strings,
                "error": strings["auth"].get("account_inactive", "Account is inactive"),
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )
    token = auth_manager.create_access_token(user.email)

    session.add(ActivityLog(user_id=user.id, action="login"))
    session.commit()
    redirect_to = "/dashboard" if user.role != UserRole.SUPER_ADMIN else "/super-admin"
    redirect_response = RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.set_login_cookie(redirect_response, token)
    return redirect_response


@router.get("/signup")
def signup_page(request: Request):
    locale = getattr(request.state, "locale", request.query_params.get("lang", "ko"))
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
def logout():
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.clear_login_cookie(redirect_response)
    return redirect_response
