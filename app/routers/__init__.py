# Auth router uses the modular auth/ package.
# The legacy monolithic auth.py has been renamed to auth_legacy.py for reference.
from . import admin, dashboard, subscriptions
from .auth import router as auth_router

__all__ = ["admin", "auth_router", "dashboard", "subscriptions"]
