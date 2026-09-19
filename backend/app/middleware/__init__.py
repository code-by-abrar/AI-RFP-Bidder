# backend/app/middleware/__init__.py
from backend.app.middleware.auth import get_current_user

__all__ = ["get_current_user"]
