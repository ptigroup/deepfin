"""Global exception handlers for consistent error responses.

Exception handlers in FastAPI allow you to:
- Convert Python exceptions to HTTP error responses
- Return consistent error format across all endpoints
- Hide sensitive error details in production
- Log exceptions with context
- Map different exception types to appropriate HTTP status codes

Benefits:
- API consumers get predictable error format
- Sensitive data (stack traces, DB errors) not leaked
- Easier debugging with structured error responses
- Consistent error handling without repetitive try/except blocks
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def create_error_response(
    request: Request,
    status_code: int,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Create a standardized error response.

    Args:
        request: The incoming request
        status_code: HTTP status code
        message: User-friendly error message
        details: Optional additional error details (only in development)

    Returns:
        JSONResponse with standardized error format
    """
    request_id = getattr(request.state, "request_id", "unknown")

    error_response: dict[str, Any] = {
        "success": False,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": request_id,
    }

    # Include detailed error information only in development
    if settings.is_development and details:
        error_response["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=error_response,
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors.

    Pydantic ValidationError occurs when:
    - Request body doesn't match schema
    - Query parameters have wrong types
    - Path parameters are invalid

    Args:
        request: The incoming request
        exc: The validation error from Pydantic

    Returns:
        422 Unprocessable Entity with validation error details

    Example Response:
        {
            "success": false,
            "message": "Validation error",
            "timestamp": "2025-12-18T10:30:00Z",
            "request_id": "abc-123-xyz",
            "details": [
                {
                    "loc": ["body", "name"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
    """
    logger.warning(
        "Validation error",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )

    return create_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error",
        details=exc.errors() if settings.is_development else None,
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors.

    SQLAlchemyError occurs when:
    - Database connection fails
    - SQL query is invalid
    - Database constraint violation
    - Transaction deadlock

    Args:
        request: The incoming request
        exc: The SQLAlchemy error

    Returns:
        500 Internal Server Error with safe error message

    Note:
        Database error details are logged but not exposed to clients
        to prevent information disclosure vulnerabilities.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "Database error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
        exc_info=True,
    )

    # Don't expose database details to clients (security risk)
    return create_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Database error occurred",
        details=str(exc) if settings.is_development else None,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other uncaught exceptions.

    This is the catch-all handler for any exception not handled by
    other specific handlers. It ensures the API always returns
    a structured JSON response, never a plain text error or stack trace.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        500 Internal Server Error with generic error message

    Note:
        Full exception details are logged for debugging but not
        exposed to clients in production.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
        exc_info=True,
    )

    return create_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        details=str(exc) if settings.is_development else None,
    )
