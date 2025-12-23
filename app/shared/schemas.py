"""Base Pydantic schemas for API requests and responses.

This module provides:
- Base schema configurations
- Timestamp schema mixin
- Common field validators

Example:
    from app.shared.schemas import TimestampSchema
    from pydantic import BaseModel, ConfigDict

    class UserResponse(TimestampSchema):
        id: int
        email: str
        # created_at and updated_at automatically included from TimestampSchema
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration.

    This schema provides:
    - ORM mode for SQLAlchemy model conversion
    - Validation on assignment
    - JSON serialization support

    Example:
        class UserBase(BaseSchema):
            email: str
            name: str

        # Can create from ORM model:
        user_orm = User(email="test@example.com", name="Test")
        user_schema = UserBase.model_validate(user_orm)
    """

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy models
        validate_assignment=True,  # Validate on attribute assignment
        str_strip_whitespace=True,  # Strip whitespace from strings
        json_schema_extra={
            "examples": [{}]  # Placeholder for OpenAPI examples
        },
    )


class TimestampSchema(BaseSchema):
    """Schema mixin that includes timestamp fields.

    This schema includes:
    - created_at: When the record was created
    - updated_at: When the record was last modified

    Use this as a base for response schemas that include database models
    with TimestampMixin.

    Example:
        class UserResponse(TimestampSchema):
            id: int
            email: str
            name: str

        # Response will include: id, email, name, created_at, updated_at
    """

    created_at: datetime = Field(
        ...,
        description="Timestamp when the record was created",
        json_schema_extra={"example": "2025-01-01T00:00:00Z"},
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when the record was last updated",
        json_schema_extra={"example": "2025-01-01T00:00:00Z"},
    )


class PaginationParams(BaseSchema):
    """Common pagination parameters for list endpoints.

    Attributes:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Example:
        @app.get("/users")
        async def list_users(
            skip: int = 0,
            limit: int = 100,
            db: AsyncSession = Depends(get_db)
        ):
            result = await db.execute(
                select(User).offset(skip).limit(limit)
            )
            return result.scalars().all()
    """

    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip",
        json_schema_extra={"example": 0},
    )

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return",
        json_schema_extra={"example": 100},
    )


class BaseResponse(BaseSchema):
    """Base response schema for all API responses.

    Provides consistent response format with success status and optional message.

    Attributes:
        success: Whether the operation was successful
        message: Optional message about the operation
        timestamp: When the response was generated

    Example:
        class UserResponse(BaseResponse):
            data: UserSchema

        return UserResponse(
            success=True,
            message="User retrieved successfully",
            data=user
        )
    """

    success: bool = Field(default=True, description="Whether the operation was successful")
    message: str | None = Field(default=None, description="Optional message about the operation")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the response was generated",
    )


class ErrorResponse(BaseSchema):
    """Standard error response schema.

    Provides consistent error format across all API endpoints.

    Attributes:
        detail: Human-readable error message
        error_code: Machine-readable error code (optional)

    Example:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                detail="User not found",
                error_code="USER_NOT_FOUND"
            ).model_dump()
        )
    """

    detail: str = Field(
        ...,
        description="Human-readable error message",
        json_schema_extra={"example": "An error occurred"},
    )

    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code",
        json_schema_extra={"example": "VALIDATION_ERROR"},
    )
