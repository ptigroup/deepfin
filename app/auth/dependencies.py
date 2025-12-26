"""FastAPI dependencies for authentication."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.service import AuthService, AuthServiceError
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer token scheme (Authorization: Bearer <token>)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token.

    This dependency:
    1. Extracts JWT token from Authorization header
    2. Validates and decodes the token
    3. Fetches user from database
    4. Verifies user is active

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException 401: If token is invalid or user not found

    Example:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"message": f"Hello {current_user.email}"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token
        token = credentials.credentials

        # Decode and validate token
        token_data = AuthService.decode_access_token(token)

        # Get user from database
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(token_data.user_id)

        if user is None:
            logger.warning(
                "Token valid but user not found",
                extra={"user_id": token_data.user_id},
            )
            raise credentials_exception

        if not user.is_active:
            logger.warning(
                "Token valid but user is inactive",
                extra={"user_id": user.id, "email": user.email},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        return user

    except AuthServiceError as e:
        logger.error(
            "Authentication error",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise credentials_exception from e

    except Exception as e:
        logger.error(
            "Unexpected error in get_current_user",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise credentials_exception from e


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user.

    Additional check on top of get_current_user to ensure user is active.
    (Actually redundant since get_current_user already checks this, but
    included for clarity and future-proofing.)

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Current active user

    Raises:
        HTTPException 403: If user is inactive

    Example:
        @router.get("/admin")
        async def admin_route(
            current_user: User = Depends(get_current_active_user)
        ):
            return {"message": "Admin access granted"}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current superuser.

    Only allows superusers to access the route.

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        Current superuser

    Raises:
        HTTPException 403: If user is not a superuser

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: User = Depends(get_current_superuser)
        ):
            # Only superusers can delete users
            return {"message": f"User {user_id} deleted"}
    """
    if not current_user.is_superuser:
        logger.warning(
            "Non-superuser attempted to access superuser-only endpoint",
            extra={"user_id": current_user.id, "email": current_user.email},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
