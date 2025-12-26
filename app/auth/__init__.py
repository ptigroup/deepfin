"""Authentication and authorization module."""

from app.auth.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
)
from app.auth.models import User
from app.auth.routes import router
from app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    Token,
    TokenData,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.auth.service import AuthService, AuthServiceError

__all__ = [
    # Models
    "User",
    # Service
    "AuthService",
    "AuthServiceError",
    # Schemas
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "TokenData",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    # Router
    "router",
]
