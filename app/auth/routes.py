"""REST API endpoints for authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_current_superuser
from app.auth.models import User
from app.auth.schemas import LoginRequest, RegisterRequest, Token, UserCreate, UserResponse
from app.auth.service import AuthService, AuthServiceError
from app.core.database import get_db
from app.core.logging import get_logger
from app.shared.schemas import BaseResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Register a new user account.

    Creates a new user with hashed password and returns user details (no token).
    User must login separately to get an access token.

    Args:
        user_data: Registration data (email, password, optional username)
        db: Database session

    Returns:
        Created user details (no sensitive data)

    Raises:
        HTTPException 400: If email/username already exists
        HTTPException 500: If registration fails

    Example:
        POST /auth/register
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "username": "john_doe"
        }

        Response:
        {
            "success": true,
            "message": "User registered successfully",
            "data": {
                "id": 1,
                "email": "user@example.com",
                "username": "john_doe",
                "is_active": true,
                "is_superuser": false,
                ...
            }
        }
    """
    try:
        auth_service = AuthService(db)

        user_create = UserCreate(
            email=user_data.email,
            password=user_data.password,
            username=user_data.username,
            is_active=True,
            is_superuser=False,
        )

        user = await auth_service.create_user(user_create)

        logger.info(
            "User registered successfully",
            extra={"user_id": user.id, "email": user.email},
        )

        return {
            "success": True,
            "message": "User registered successfully",
            "data": UserResponse.model_validate(user).model_dump(),
        }

    except AuthServiceError as e:
        logger.error(
            "Registration failed",
            extra={"email": user_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected registration error",
            extra={"email": user_data.email, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        ) from e


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Login with email and password to get JWT access token.

    Authenticates user and returns JWT token for accessing protected routes.

    Args:
        login_data: Login credentials (email, password)
        db: Database session

    Returns:
        JWT access token with expiration info

    Raises:
        HTTPException 401: If credentials are invalid

    Example:
        POST /auth/login
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }

        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }

        Usage:
        Include token in subsequent requests:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    try:
        auth_service = AuthService(db)

        access_token, expires_in = await auth_service.login(
            email=login_data.email,
            password=login_data.password,
        )

        logger.info(
            "User logged in successfully",
            extra={"email": login_data.email},
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }

    except AuthServiceError as e:
        logger.warning(
            "Login failed",
            extra={"email": login_data.email, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected login error",
            extra={"email": login_data.email, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        ) from e


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get current authenticated user's information.

    Protected endpoint that returns details about the currently logged-in user.
    Requires valid JWT token in Authorization header.

    Args:
        current_user: Current user (from JWT token)

    Returns:
        Current user details

    Example:
        GET /auth/me
        Headers: Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "email": "user@example.com",
                "username": "john_doe",
                "is_active": true,
                "is_superuser": false,
                "created_at": "2025-12-26T08:00:00Z",
                "updated_at": "2025-12-26T08:00:00Z"
            }
        }
    """
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user).model_dump(),
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Refresh JWT access token.

    Generate a new JWT token using an existing valid token.
    Useful for extending user sessions without re-login.

    Args:
        current_user: Current user (from existing JWT token)

    Returns:
        New JWT access token with expiration info

    Example:
        POST /auth/refresh
        Headers: Authorization: Bearer <old_token>

        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    """
    # Create new token for current user
    from app.core.config import get_settings

    settings = get_settings()

    access_token = AuthService.create_access_token(
        user_id=current_user.id,
        email=current_user.email,
    )

    expires_in = settings.access_token_expire_minutes * 60

    logger.info(
        "Token refreshed",
        extra={"user_id": current_user.id, "email": current_user.email},
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.get("/users/{user_id}", response_model=BaseResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get user by ID (superuser only).

    Admin endpoint for retrieving any user's details.

    Args:
        user_id: User ID to fetch
        current_user: Current superuser (verified by dependency)
        db: Database session

    Returns:
        User details

    Raises:
        HTTPException 403: If user is not superuser
        HTTPException 404: If user not found

    Example:
        GET /auth/users/1
        Headers: Authorization: Bearer <admin_token>

        Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "email": "user@example.com",
                ...
            }
        }
    """
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    return {
        "success": True,
        "data": UserResponse.model_validate(user).model_dump(),
    }
