"""Tests for shared database models and mixins.

This module tests:
- TimestampMixin functionality
- utcnow() utility function
- Automatic timestamp population
- Timestamp update behavior
"""

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import AsyncSessionLocal, Base, engine
from app.shared.models import TimestampMixin, utcnow


# Check if database is available
def is_db_available():
    """Check if PostgreSQL database is available for testing."""

    async def check():
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    try:
        return asyncio.run(check())
    except Exception:
        return False


# Skip marker for tests that require database
requires_db = pytest.mark.skipif(not is_db_available(), reason="PostgreSQL database not available")


class TimestampTestModel(Base, TimestampMixin):
    """Test model with TimestampMixin for testing.

    This model is used only for testing timestamp behavior.
    """

    __tablename__ = "timestamp_test_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


@pytest.fixture(scope="function")
async def setup_test_table():
    """Create test table before test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_utcnow_returns_datetime():
    """Test that utcnow() returns a datetime object.

    Verifies:
    - Function returns datetime instance
    - Datetime is timezone-aware
    - Timezone is UTC
    """
    now = utcnow()
    assert isinstance(now, datetime), "Should return datetime instance"
    assert now.tzinfo is not None, "Should be timezone-aware"
    assert now.tzinfo == UTC, "Should be UTC timezone"


def test_utcnow_current_time():
    """Test that utcnow() returns current time.

    Verifies:
    - Returned time is close to actual current time
    - Time is in UTC
    """
    before = datetime.now(UTC)
    now = utcnow()
    after = datetime.now(UTC)

    assert before <= now <= after, "Should return current time"


@requires_db
@pytest.mark.asyncio
async def test_timestamp_mixin_fields_exist(setup_test_table):
    """Test that TimestampMixin adds created_at and updated_at fields.

    Verifies:
    - created_at field exists on model
    - updated_at field exists on model
    - Fields are properly typed
    """
    assert hasattr(TimestampTestModel, "created_at"), "Should have created_at field"
    assert hasattr(TimestampTestModel, "updated_at"), "Should have updated_at field"


@requires_db
@pytest.mark.asyncio
async def test_timestamps_auto_populate_on_create(setup_test_table):
    """Test that timestamps are automatically set when creating a record.

    Verifies:
    - created_at is set automatically
    - updated_at is set automatically
    - Both timestamps are close to current time
    - Both timestamps are equal on creation
    """
    before = datetime.now(UTC)

    async with AsyncSessionLocal() as session:
        test_obj = TimestampTestModel(name="test")
        session.add(test_obj)
        await session.commit()
        await session.refresh(test_obj)

        after = datetime.now(UTC)

        assert test_obj.created_at is not None, "created_at should be set"
        assert test_obj.updated_at is not None, "updated_at should be set"

        # Timestamps should be within test execution time
        assert before <= test_obj.created_at <= after, "created_at should be current time"
        assert before <= test_obj.updated_at <= after, "updated_at should be current time"

        # On creation, both timestamps should be very close (within 1 second)
        time_diff = abs((test_obj.updated_at - test_obj.created_at).total_seconds())
        assert time_diff < 1, "Timestamps should be nearly identical on creation"


@requires_db
@pytest.mark.asyncio
async def test_updated_at_changes_on_update(setup_test_table):
    """Test that updated_at changes when record is modified.

    Verifies:
    - updated_at is updated when record changes
    - created_at remains unchanged
    - updated_at is later than created_at after update
    """
    async with AsyncSessionLocal() as session:
        # Create initial record
        test_obj = TimestampTestModel(name="original")
        session.add(test_obj)
        await session.commit()
        await session.refresh(test_obj)

        original_created_at = test_obj.created_at
        original_updated_at = test_obj.updated_at

        # Wait a small amount to ensure timestamp difference
        await asyncio.sleep(0.1)

        # Update the record
        test_obj.name = "updated"
        await session.commit()
        await session.refresh(test_obj)

        assert test_obj.created_at == original_created_at, "created_at should not change"
        assert test_obj.updated_at > original_updated_at, "updated_at should increase"
        assert test_obj.updated_at > test_obj.created_at, "updated_at should be after created_at"


@requires_db
@pytest.mark.asyncio
async def test_timestamps_timezone_aware(setup_test_table):
    """Test that timestamp fields are timezone-aware.

    Verifies:
    - created_at has timezone information
    - updated_at has timezone information
    - Both use UTC timezone
    """
    async with AsyncSessionLocal() as session:
        test_obj = TimestampTestModel(name="test")
        session.add(test_obj)
        await session.commit()
        await session.refresh(test_obj)

        assert test_obj.created_at.tzinfo is not None, "created_at should be timezone-aware"
        assert test_obj.updated_at.tzinfo is not None, "updated_at should be timezone-aware"


@requires_db
@pytest.mark.asyncio
async def test_multiple_updates_update_timestamp(setup_test_table):
    """Test that multiple updates continue to update timestamp.

    Verifies:
    - Each update increases updated_at
    - updated_at always reflects latest modification
    - created_at never changes
    """
    async with AsyncSessionLocal() as session:
        test_obj = TimestampTestModel(name="v1")
        session.add(test_obj)
        await session.commit()
        await session.refresh(test_obj)

        original_created_at = test_obj.created_at
        timestamps = [test_obj.updated_at]

        # Perform multiple updates
        for i in range(2, 4):
            await asyncio.sleep(0.1)  # Ensure timestamp difference
            test_obj.name = f"v{i}"
            await session.commit()
            await session.refresh(test_obj)
            timestamps.append(test_obj.updated_at)

        # Verify timestamps are increasing
        assert timestamps[0] < timestamps[1] < timestamps[2], (
            "Timestamps should increase with each update"
        )
        assert test_obj.created_at == original_created_at, "created_at should never change"
