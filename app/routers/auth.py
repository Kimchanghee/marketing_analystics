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
    status_flag = request.query_params.get("status")
    success_message = None
    if status_flag == "signup_success":
        success_message = strings["auth"].get("signup_success", "계정이 생성되었습니다. 로그인하세요.")
    return request.app.state.templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "success": success_message,
            "error": None,
        },
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
                "success": None,
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
                "success": None,
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
    role_param = request.query_params.get("role")
    try:
        selected_role = UserRole(role_param) if role_param else UserRole.CREATOR
    except ValueError:
        selected_role = UserRole.CREATOR
    form_defaults = {
        "email": request.query_params.get("email", ""),
        "organization": request.query_params.get("organization", ""),
        "role": selected_role.value,
        "locale": locale,
    }
    return request.app.state.templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
            "locale": locale,
            "t": strings,
            "form": form_defaults,
            "error": None,
        },
    )


@router.post("/signup")
def signup(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...),
    role: UserRole = Form(UserRole.CREATOR),
    locale: str = Form("ko"),
    organization: str | None = Form(None),
    session=Depends(get_session),
):
    request_locale = getattr(request.state, "locale", locale)
    strings = translator.load_locale(request_locale)

    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        form_data = {
            "email": str(email),
            "organization": organization or "",
            "role": role.value,
            "locale": locale,
        }
        return request.app.state.templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "locale": request_locale,
                "t": strings,
                "form": form_data,
                "error": strings["auth"].get("email_exists", "이미 등록된 이메일입니다."),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

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

    redirect_response = RedirectResponse(
        url="/login?status=signup_success",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    return redirect_response


@router.post("/logout")
def logout():
    redirect_response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    auth_manager.clear_login_cookie(redirect_response)
    return redirect_response
