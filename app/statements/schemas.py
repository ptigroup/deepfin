"""Pydantic schemas for financial statements."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.shared.schemas import BaseResponse
from app.statements.models import StatementType


class LineItemCreate(BaseModel):
    """Schema for creating a line item."""

    statement_id: int = Field(..., gt=0, description="ID of the parent statement")
    line_item_name: str = Field(
        ..., min_length=1, max_length=500, description="Name of the line item"
    )
    category: str | None = Field(None, max_length=100, description="Category for grouping")
    value: Decimal = Field(..., description="Numeric value for this line item")
    indent_level: int = Field(default=0, ge=0, le=5, description="Indentation level (0-5)")
    order: int = Field(..., ge=0, description="Display order within the statement")
    parent_id: int | None = Field(None, gt=0, description="Optional parent line item ID")
    notes: str | None = Field(None, description="Optional notes or annotations")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Decimal) -> Decimal:
        """Validate that value has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("value must have at most 2 decimal places")
        return v


class LineItemUpdate(BaseModel):
    """Schema for updating a line item."""

    line_item_name: str | None = Field(None, min_length=1, max_length=500)
    category: str | None = Field(None, max_length=100)
    value: Decimal | None = None
    indent_level: int | None = Field(None, ge=0, le=5)
    order: int | None = Field(None, ge=0)
    parent_id: int | None = Field(None, gt=0)
    notes: str | None = None

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Decimal | None) -> Decimal | None:
        """Validate that value has at most 2 decimal places."""
        if v is not None and v.as_tuple().exponent < -2:
            raise ValueError("value must have at most 2 decimal places")
        return v


class LineItemSchema(BaseModel):
    """Schema for line item response."""

    id: int
    statement_id: int
    line_item_name: str
    category: str | None
    value: Decimal
    indent_level: int
    order: int
    parent_id: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatementCreate(BaseModel):
    """Schema for creating a statement."""

    statement_type: StatementType = Field(..., description="Type of financial statement")
    company_name: str = Field(..., min_length=1, max_length=255, description="Name of the company")
    period_start: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD format)",
    )
    period_end: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD format)",
    )
    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="Currency code (ISO 4217)",
    )
    fiscal_year: int = Field(..., gt=1900, le=2100, description="Fiscal year")
    extra_metadata: str | None = Field(None, description="Additional metadata as JSON text")

    @field_validator("period_start", "period_end")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        if len(v) != 10:
            raise ValueError("Date must be in YYYY-MM-DD format")
        parts = v.split("-")
        if len(parts) != 3:
            raise ValueError("Date must be in YYYY-MM-DD format")
        year, month, day = parts
        if not (year.isdigit() and month.isdigit() and day.isdigit()):
            raise ValueError("Date must contain only digits and hyphens")
        if not (1 <= int(month) <= 12):
            raise ValueError("Month must be between 01 and 12")
        if not (1 <= int(day) <= 31):
            raise ValueError("Day must be between 01 and 31")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency is uppercase 3-letter code."""
        if not v.isupper():
            raise ValueError("Currency code must be uppercase")
        if len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")
        return v


class StatementUpdate(BaseModel):
    """Schema for updating a statement."""

    statement_type: StatementType | None = None
    company_name: str | None = Field(None, min_length=1, max_length=255)
    period_start: str | None = Field(
        None, min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    period_end: str | None = Field(
        None, min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    currency: str | None = Field(None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    fiscal_year: int | None = Field(None, gt=1900, le=2100)
    extra_metadata: str | None = None

    @field_validator("period_start", "period_end")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date format is YYYY-MM-DD."""
        if v is None:
            return v
        if len(v) != 10:
            raise ValueError("Date must be in YYYY-MM-DD format")
        parts = v.split("-")
        if len(parts) != 3:
            raise ValueError("Date must be in YYYY-MM-DD format")
        year, month, day = parts
        if not (year.isdigit() and month.isdigit() and day.isdigit()):
            raise ValueError("Date must contain only digits and hyphens")
        if not (1 <= int(month) <= 12):
            raise ValueError("Month must be between 01 and 12")
        if not (1 <= int(day) <= 31):
            raise ValueError("Day must be between 01 and 31")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency is uppercase 3-letter code."""
        if v is None:
            return v
        if not v.isupper():
            raise ValueError("Currency code must be uppercase")
        if len(v) != 3:
            raise ValueError("Currency code must be exactly 3 characters")
        return v


class StatementSchema(BaseModel):
    """Schema for statement response."""

    id: int
    statement_type: StatementType
    company_name: str
    period_start: str
    period_end: str
    currency: str
    fiscal_year: int
    extra_metadata: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatementWithLineItems(StatementSchema):
    """Schema for statement with line items."""

    line_items: list[LineItemSchema] = []

    model_config = {"from_attributes": True}


class StatementResponse(BaseResponse):
    """Response schema for statement."""

    data: StatementSchema


class StatementListResponse(BaseResponse):
    """Response schema for list of statements."""

    data: list[StatementSchema]
    total: int = 0


class LineItemResponse(BaseResponse):
    """Response schema for line item."""

    data: LineItemSchema


class LineItemListResponse(BaseResponse):
    """Response schema for list of line items."""

    data: list[LineItemSchema]
    total: int = 0
