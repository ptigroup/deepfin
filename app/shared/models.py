"""Reusable database model mixins and utilities.

This module provides:
- TimestampMixin: Automatic created_at/updated_at timestamps
- utcnow(): UTC datetime utility function

Example:
    from app.core.database import Base
    from app.shared.models import TimestampMixin

    class User(Base, TimestampMixin):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        email: Mapped[str] = mapped_column(String(255))
        # created_at and updated_at automatically included via TimestampMixin
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Get current UTC datetime.

    This function provides a consistent way to get UTC timestamps across
    the application, ensuring timezone-aware datetime objects.

    Returns:
        datetime: Current UTC time with timezone information

    Example:
        >>> now = utcnow()
        >>> print(now.tzinfo)
        datetime.timezone.utc
    """
    return datetime.now(UTC)


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns.

    This mixin automatically:
    - Sets created_at when a record is inserted
    - Updates updated_at whenever a record is modified
    - Uses UTC timezone for all timestamps
    - Handles timestamps at the database level for consistency

    Attributes:
        created_at: Timestamp when record was created (set once, never changes)
        updated_at: Timestamp when record was last modified (auto-updates)

    Example:
        class User(Base, TimestampMixin):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            email: Mapped[str]

        # When you create a user:
        user = User(email="test@example.com")
        db.add(user)
        await db.commit()
        # created_at and updated_at are automatically set

        # When you update a user:
        user.email = "new@example.com"
        await db.commit()
        # updated_at is automatically updated, created_at stays the same
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when the record was last updated",
    )
