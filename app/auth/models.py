"""User authentication models."""

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin


class User(Base, TimestampMixin):
    """User account model.

    Represents an authenticated user in the system with password-based
    authentication. Supports both email and optional username login.

    Attributes:
        id: Primary key
        email: Unique email address (required, used for login)
        username: Optional username (unique if provided)
        hashed_password: Bcrypt-hashed password (never store plaintext!)
        is_active: Whether user account is active (for soft deletion/suspension)
        is_superuser: Whether user has admin privileges
        created_at: When account was created (via TimestampMixin)
        updated_at: When account was last modified (via TimestampMixin)

    Example:
        # Create new user (password should be hashed first!)
        from app.auth.service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.create_user(
            email="user@example.com",
            password="secret123"  # Will be hashed by service
        )

        # Login
        token = await auth_service.login(
            email="user@example.com",
            password="secret123"
        )
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="User ID (primary key)",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User email address (unique, used for login)",
    )

    username: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        doc="Optional username (unique if provided)",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt-hashed password (NEVER store plaintext!)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="Whether user account is active",
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="Whether user has admin/superuser privileges",
    )

    # Composite index for common query patterns
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_username_active", "username", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, active={self.is_active})>"
