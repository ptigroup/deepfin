"""Middleware for request processing, logging, and tracing.

Middleware in FastAPI runs before and after each request, allowing you to:
- Add request context (request IDs, user info)
- Log request/response details
- Measure request duration
- Add custom headers
- Handle cross-cutting concerns

Middleware execution order:
    Request → Middleware 1 (before) → Middleware 2 (before) → Endpoint
    → Middleware 2 (after) → Middleware 1 (after) → Response
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a unique ID to each request.

    Request IDs are critical for:
    - Debugging: Track a single request through logs
    - Distributed tracing: Connect logs across microservices
    - Support: Users can provide request ID when reporting issues

    The request ID is:
    - Generated as a UUID4 for each request
    - Stored in request.state for access in endpoints
    - Added to response headers as X-Request-ID
    - Included in all log messages for that request
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process request and add request ID.

        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/endpoint

        Returns:
            Response with X-Request-ID header added
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for access in endpoints/logging
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers for client tracking
        response.headers["X-Request-ID"] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all requests and responses.

    Logs include:
    - HTTP method and path
    - Request ID for traceability
    - Response status code
    - Request duration in milliseconds
    - Client IP address

    This provides observability for:
    - Performance monitoring (slow requests)
    - Error tracking (4xx, 5xx responses)
    - Usage analytics (endpoint popularity)
    - Security auditing (suspicious patterns)
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process request and log details.

        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/endpoint

        Returns:
            Response after processing and logging
        """
        # Get request ID (added by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", "unknown")

        # Record start time for duration calculation
        start_time = time.time()

        # Log request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000

            # Log successful request completion
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            return response

        except Exception as e:
            # Calculate duration even for failed requests
            duration_ms = (time.time() - start_time) * 1000

            # Log request failure
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )

            # Re-raise exception to be handled by exception handlers
            raise
