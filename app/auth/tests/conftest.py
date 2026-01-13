"""Pytest fixtures for auth tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock database session for testing.

    Returns:
        Mocked AsyncSession
    """
    db = AsyncMock(spec=AsyncSession)

    # Mock user storage
    users_db: dict[int, User] = {}
    user_id_counter = [1]  # Use list for mutable counter

    async def mock_add(user: User):
        """Mock adding user to database."""
        if user.id is None:
            user.id = user_id_counter[0]
            user_id_counter[0] += 1
        users_db[user.id] = user

    async def mock_commit():
        """Mock commit (no-op)."""
        pass

    async def mock_rollback():
        """Mock rollback (no-op)."""
        pass

    async def mock_refresh(user: User):
        """Mock refresh (no-op)."""
        pass

    async def mock_execute(stmt):
        """Mock execute for SELECT queries."""
        result = MagicMock()

        # Parse the WHERE clause to determine what we're querying
        where_clauses = str(stmt.whereclause) if hasattr(stmt, "whereclause") else ""

        if "users.id" in where_clauses:
            # Query by ID
            for user in users_db.values():
                if f"users.id = {user.id}" in where_clauses:
                    result.scalar_one_or_none.return_value = user
                    return result
            result.scalar_one_or_none.return_value = None

        elif "users.email" in where_clauses:
            # Query by email
            for user in users_db.values():
                if user.email in where_clauses:
                    result.scalar_one_or_none.return_value = user
                    return result
            result.scalar_one_or_none.return_value = None

        elif "users.username" in where_clauses:
            # Query by username
            for user in users_db.values():
                if user.username and user.username in where_clauses:
                    result.scalar_one_or_none.return_value = user
                    return result
            result.scalar_one_or_none.return_value = None

        else:
            result.scalar_one_or_none.return_value = None

        return result

    db.add = mock_add
    db.commit = mock_commit
    db.rollback = mock_rollback
    db.refresh = mock_refresh
    db.execute = mock_execute

    return db
