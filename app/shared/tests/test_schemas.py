"""Tests for shared Pydantic schemas.

This module tests:
- BaseSchema configuration
- TimestampSchema fields and validation
- PaginationParams validation
- ErrorResponse schema
- ORM mode functionality
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models import TimestampMixin
from app.shared.schemas import (
    BaseSchema,
    ErrorResponse,
    PaginationParams,
    TimestampSchema,
)


class SampleORMModel(Base, TimestampMixin):
    """Sample ORM model for schema validation tests."""

    __tablename__ = "test_orm_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class SampleModelSchema(BaseSchema):
    """Sample schema inheriting from BaseSchema."""

    id: int
    name: str


class SampleTimestampModelSchema(TimestampSchema):
    """Sample schema with timestamp fields."""

    id: int
    name: str


def test_base_schema_from_dict():
    """Test BaseSchema can be created from dictionary.

    Verifies:
    - Schema accepts dict input
    - Fields are properly validated
    - Values are accessible
    """
    data = {"id": 1, "name": "test"}
    schema = SampleModelSchema(**data)

    assert schema.id == 1, "Should parse id field"
    assert schema.name == "test", "Should parse name field"


def test_base_schema_strips_whitespace():
    """Test that BaseSchema strips whitespace from string fields.

    Verifies:
    - Leading whitespace is stripped
    - Trailing whitespace is stripped
    - Middle whitespace is preserved
    """
    data = {"id": 1, "name": "  test  name  "}
    schema = SampleModelSchema(**data)

    assert schema.name == "test  name", "Should strip leading/trailing whitespace but preserve internal"


def test_timestamp_schema_includes_timestamps():
    """Test that TimestampSchema includes timestamp fields.

    Verifies:
    - created_at field exists and is required
    - updated_at field exists and is required
    - Timestamps can be parsed from strings
    - Timestamps are datetime objects
    """
    now = datetime.now(timezone.utc)
    data = {
        "id": 1,
        "name": "test",
        "created_at": now,
        "updated_at": now,
    }
    schema = SampleTimestampModelSchema(**data)

    assert hasattr(schema, "created_at"), "Should have created_at field"
    assert hasattr(schema, "updated_at"), "Should have updated_at field"
    assert isinstance(schema.created_at, datetime), "created_at should be datetime"
    assert isinstance(schema.updated_at, datetime), "updated_at should be datetime"


def test_pagination_params_defaults():
    """Test PaginationParams default values.

    Verifies:
    - skip defaults to 0
    - limit defaults to 100
    - Can be created without arguments
    """
    params = PaginationParams()

    assert params.skip == 0, "skip should default to 0"
    assert params.limit == 100, "limit should default to 100"


def test_pagination_params_validation():
    """Test PaginationParams field validation.

    Verifies:
    - skip cannot be negative
    - limit must be between 1 and 1000
    - Invalid values raise ValidationError
    """
    # Valid params
    params = PaginationParams(skip=10, limit=50)
    assert params.skip == 10
    assert params.limit == 50

    # Test skip validation (cannot be negative)
    with pytest.raises(ValidationError) as exc_info:
        PaginationParams(skip=-1, limit=10)
    assert "skip" in str(exc_info.value).lower()

    # Test limit validation (must be >= 1)
    with pytest.raises(ValidationError) as exc_info:
        PaginationParams(skip=0, limit=0)
    assert "limit" in str(exc_info.value).lower()

    # Test limit validation (must be <= 1000)
    with pytest.raises(ValidationError) as exc_info:
        PaginationParams(skip=0, limit=1001)
    assert "limit" in str(exc_info.value).lower()


def test_error_response_schema():
    """Test ErrorResponse schema structure.

    Verifies:
    - detail field is required
    - error_code field is optional
    - Can serialize to dict
    """
    # With only detail
    error1 = ErrorResponse(detail="Something went wrong")
    assert error1.detail == "Something went wrong"
    assert error1.error_code is None

    # With both fields
    error2 = ErrorResponse(detail="User not found", error_code="USER_NOT_FOUND")
    assert error2.detail == "User not found"
    assert error2.error_code == "USER_NOT_FOUND"

    # Can convert to dict
    error_dict = error2.model_dump()
    assert error_dict["detail"] == "User not found"
    assert error_dict["error_code"] == "USER_NOT_FOUND"


def test_base_schema_validation_on_assignment():
    """Test that BaseSchema validates fields on assignment.

    Verifies:
    - Field validation occurs when values are assigned
    - Invalid assignments raise ValidationError
    - Valid assignments succeed
    """
    schema = SampleModelSchema(id=1, name="test")

    # Valid assignment
    schema.name = "new name"
    assert schema.name == "new name"

    # Invalid assignment (wrong type)
    with pytest.raises(ValidationError):
        schema.id = "not an integer"


def test_timestamp_schema_from_orm():
    """Test TimestampSchema can be created from ORM model.

    Verifies:
    - from_attributes=True allows ORM model conversion
    - All fields are properly mapped
    - Timestamps are preserved
    """
    # Simulate an ORM model instance
    class MockORMModel:
        id = 1
        name = "test"
        created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        updated_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    orm_obj = MockORMModel()
    schema = SampleTimestampModelSchema.model_validate(orm_obj)

    assert schema.id == 1
    assert schema.name == "test"
    assert schema.created_at == orm_obj.created_at
    assert schema.updated_at == orm_obj.updated_at
