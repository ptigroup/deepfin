"""Database infrastructure with async SQLAlchemy 2.0.

This module provides:
- Async database engine with connection pooling
- Session factory for database operations
- Base model class for all ORM models
- FastAPI dependency for database sessions

Example:
    from app.core.database import get_db
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User))
        return result.scalars().all()
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models.

    All database models should inherit from this class to gain:
    - Automatic table name generation
    - Metadata tracking for migrations
    - Type checking support with Mapped[]

    Example:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            email: Mapped[str] = mapped_column(String(255), unique=True)
    """

    pass


# Get database configuration from settings
settings = get_settings()

# Create async engine with connection pooling
# pool_size: Number of connections to maintain
# max_overflow: Additional connections when pool is exhausted
# echo: Log all SQL statements (useful for debugging)
engine = create_async_engine(
    str(settings.database_url),  # Convert PostgresDsn to string
    echo=settings.database_echo,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory for creating database sessions
# expire_on_commit=False: Keep objects accessible after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides database sessions.

    This dependency handles:
    - Session creation and cleanup
    - Automatic commit on success
    - Automatic rollback on exceptions
    - Proper connection closure

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session for the request

    Raises:
        Exception: Any database errors are propagated after rollback
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.info("database.session_created")
            yield session
            await session.commit()
            logger.info("database.session_committed")
        except Exception as e:
            await session.rollback()
            logger.error(
                "database.session_rollback",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            await session.close()
            logger.debug("database.session_closed")


async def init_db() -> None:
    """Initialize database by creating all tables.

    This function creates all tables defined in models that inherit from Base.
    Should be called on application startup.

    Note:
        In production, use Alembic migrations instead of this function.
        This is primarily for development and testing.

    Example:
        @app.on_event("startup")
        async def startup():
            await init_db()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("database.tables_created")


async def close_db() -> None:
    """Close database engine and all connections.

    Should be called on application shutdown to properly clean up resources.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    await engine.dispose()
    logger.info("database.engine_disposed")
