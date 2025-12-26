"""Pydantic schemas for authentication."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Login request schema.

    Used for authenticating users via email/password.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")


class RegisterRequest(BaseModel):
    """User registration schema.

    Used for creating new user accounts.
    """

    email: EmailStr = Field(..., description="User email address (unique)")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (min 8 characters)",
    )
    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Optional username (alphanumeric, dash, underscore only)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum security requirements.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit

        Args:
            v: Password string

        Returns:
            Password if valid

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """JWT token payload data.

    Used for encoding/decoding JWT tokens.
    """

    user_id: int = Field(..., description="User ID from token")
    email: str = Field(..., description="User email from token")
    exp: datetime | None = Field(None, description="Token expiration timestamp")


class UserResponse(BaseModel):
    """Public user data response (no sensitive fields).

    Used when returning user data in API responses.
    Never includes password or other sensitive information.
    """

    id: int
    email: str
    username: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Internal user creation schema.

    Used by service layer to create users.
    """

    email: EmailStr
    password: str  # Will be hashed before storage
    username: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(BaseModel):
    """User update schema.

    All fields optional for partial updates.
    """

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=100)
    username: str | None = Field(None, min_length=3, max_length=50)
    is_active: bool | None = None
    is_superuser: bool | None = None
