"""Health check endpoints for monitoring and load balancer integration.

This module provides health check endpoints that are used by:
- Kubernetes/Docker health probes
- Load balancers (AWS ELB, nginx, etc.)
- Monitoring systems (Datadog, New Relic, etc.)

Health checks help ensure the application is:
1. Running and responsive (/health)
2. Connected to critical dependencies like database (/health/db)
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint.

    Returns a simple response indicating the service is running.
    This is a lightweight check that doesn't test external dependencies.

    Used by:
    - Load balancers for basic availability checks
    - Monitoring systems for uptime tracking
    - Quick smoke tests

    Returns:
        dict: Health status with timestamp

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2025-12-18T10:30:00.000000Z"
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/db", status_code=status.HTTP_200_OK)
async def database_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Database connectivity health check.

    Verifies that the application can connect to and query the database.
    This is a more comprehensive check that tests critical dependencies.

    Used by:
    - Load balancers for dependency checks
    - Monitoring systems for database connectivity alerts
    - Pre-deployment validation

    Args:
        db: Database session injected by FastAPI dependency injection

    Returns:
        dict: Health status with database check result

    Raises:
        HTTPException: 503 Service Unavailable if database check fails

    Example Response (Success):
        {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-12-18T10:30:00.000000Z"
        }

    Example Response (Failure):
        {
            "status": "unhealthy",
            "database": "disconnected",
            "error": "connection timeout",
            "timestamp": "2025-12-18T10:30:00.000000Z"
        }
    """
    try:
        # Execute a simple query to verify database connectivity
        # This tests both the connection pool and database responsiveness
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        # Database is not accessible - return 503 Service Unavailable
        # 503 tells load balancers to stop sending traffic temporarily
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ) from e
