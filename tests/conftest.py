"""Central fixtures for integration tests.

This module provides fixtures for integration testing:
- Real database setup/teardown using PostgreSQL
- FastAPI TestClient for HTTP testing  
- Test data fixtures
- Authentication helpers
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db
from app.main import app


# Test database URL (use SQLite for testing by default)
# SQLite is simpler and doesn't require external database server
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",  # In-memory SQLite database
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests.
    
    This fixture provides a session-scoped event loop that can be used
    across all async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Get test settings with overridden database URL.

    Returns:
        Settings with test database configuration
    """
    # Clear the cache to allow re-creation with test settings
    get_settings.cache_clear()

    # For integration tests, we need to bypass PostgreSQL validation
    # Use a PostgreSQL URL for validation, then override the engine creation
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/test"
    os.environ["EMAIL_ENABLED"] = "false"
    os.environ["DATABASE_ECHO"] = "false"

    settings = get_settings()
    return settings


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings: Settings) -> AsyncGenerator[Any, None]:
    """Create test database engine.

    Creates all tables at session start and drops them at session end.
    Uses SQLite in-memory database for testing instead of PostgreSQL.

    Args:
        test_settings: Test configuration

    Yields:
        AsyncEngine for test database
    """
    # Use SQLite for testing (override the PostgreSQL URL)
    engine = create_async_engine(
        TEST_DATABASE_URL,  # SQLite in-memory
        echo=False,
        # SQLite specific settings
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with transaction rollback.
    
    Each test gets its own session with automatic rollback after the test.
    This ensures test isolation without needing to recreate tables.
    
    Args:
        test_engine: Test database engine
        
    Yields:
        AsyncSession for testing
    """
    # Create session factory
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        # Start transaction
        async with session.begin():
            yield session
            # Rollback happens automatically when context exits


@pytest.fixture
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with database override.
    
    This client uses the test database session instead of the real one.
    
    Args:
        db_session: Test database session
        
    Yields:
        TestClient for making HTTP requests
    """
    def override_get_db() -> Generator[AsyncSession, None, None]:
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing.
    
    Use this for async tests that need to await responses.
    
    Args:
        db_session: Test database session
        
    Yields:
        AsyncClient for async HTTP requests
    """
    def override_get_db() -> Generator[AsyncSession, None, None]:
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict[str, Any]:
    """Create test user in database.
    
    Args:
        db_session: Test database session
        
    Returns:
        Dict with user information
    """
    from app.auth.models import User
    from app.auth.service import AuthService
    
    auth_service = AuthService(db_session)
    
    user = await auth_service.create_user(
        email="test@example.com",
        password="TestPassword123!",
        username="testuser",
    )
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "password": "TestPassword123!",  # Plain password for login tests
    }


@pytest_asyncio.fixture
async def auth_headers(client: TestClient, test_user: dict[str, Any]) -> dict[str, str]:
    """Get authentication headers with JWT token.
    
    Args:
        client: Test client
        test_user: Test user data
        
    Returns:
        Dict with Authorization header
    """
    # Login to get token
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"],
        },
    )
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_pdf_path() -> str:
    """Get path to sample PDF for testing.
    
    Returns:
        Path to test PDF file
    """
    # TODO: Add actual test PDF file
    return "tests/fixtures/sample_statement.pdf"


@pytest.fixture
def sample_extraction_data() -> dict[str, Any]:
    """Get sample extraction data for testing.
    
    Returns:
        Dict with sample extraction data
    """
    return {
        "statement_type": "balance_sheet",
        "company_name": "Test Company Inc.",
        "fiscal_year": 2024,
        "raw_text": "Test raw text content",
        "structured_data": {
            "accounts": [
                {
                    "account_name": "Total Assets",
                    "values": [100000, 150000],
                    "indent_level": 0,
                    "parent_section": None,
                }
            ],
            "reporting_periods": ["2023", "2024"],
        },
    }
