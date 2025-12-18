"""FastAPI application entry point.

This is the main application file that:
- Creates the FastAPI application instance
- Configures middleware (CORS, logging, request IDs)
- Registers exception handlers
- Includes API routers
- Manages application lifespan (startup/shutdown)

To run the application:
    Development:
        uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8123

    Production:
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8123 --workers 4

Access the API documentation:
    Swagger UI: http://localhost:8123/docs
    ReDoc: http://localhost:8123/redoc
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.exceptions import (
    generic_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from app.core.health import router as health_router
from app.core.logging import get_logger
from app.core.middleware import LoggingMiddleware, RequestIDMiddleware

# Initialize settings and logger
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    This context manager runs code at application startup and shutdown.

    Startup:
        - Initialize database connection
        - Run migrations (future)
        - Warm up caches (future)
        - Connect to external services (future)

    Shutdown:
        - Close database connections
        - Flush logs
        - Clean up resources

    Args:
        app: The FastAPI application instance

    Yields:
        None: Application runs during the yield
    """
    # Startup
    logger.info(
        "Application starting",
        extra={
            "environment": settings.environment,
            "debug": settings.debug,
            "version": "1.0.0",
        },
    )

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(
            "Failed to initialize database",
            extra={"error": str(e)},
            exc_info=True,
        )
        # Don't prevent startup if DB is unavailable
        # Health checks will report the issue
        logger.warning("Continuing without database connection")

    yield  # Application runs here

    # Shutdown
    logger.info("Application shutting down")

    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(
            "Error closing database connections",
            extra={"error": str(e)},
            exc_info=True,
        )


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Async financial document processing pipeline using LLMWhisperer and OpenAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Configure CORS middleware
# Must be added before other middleware to ensure CORS headers are included
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
# Order matters: RequestIDMiddleware first, then LoggingMiddleware
# This ensures request ID is available when logging
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# Register exception handlers
# These convert Python exceptions to structured JSON responses
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Include routers
# Health check endpoints for monitoring and load balancers
app.include_router(health_router)


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns:
        dict: Welcome message and documentation links

    Example Response:
        {
            "message": "LLM Financial Pipeline API",
            "docs": "/docs",
            "health": "/health"
        }
    """
    return {
        "message": "LLM Financial Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    # This allows running the app directly with: python -m app.main
    # However, using uvicorn directly is recommended for development
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8123,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
