"""Pydantic schemas for consolidation data validation and serialization."""

import re
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.shared.schemas import TimestampSchema


class ConsolidatedStatementCreate(BaseModel):
    """Schema for creating a consolidated statement."""

    name: str = Field(..., min_length=1, max_length=255, description="Consolidation name")
    description: str | None = Field(None, description="Optional description")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    start_period: str = Field(..., description="Start period (YYYY-MM-DD)")
    end_period: str = Field(..., description="End period (YYYY-MM-DD)")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    period_count: int = Field(default=0, ge=0, description="Number of periods")
    total_line_items: int = Field(default=0, ge=0, description="Total line items")
    notes: str | None = Field(None, description="Optional notes")

    @field_validator("start_period", "end_period")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")

        # Validate month and day ranges
        parts = v.split("-")
        _year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")

        if day < 1 or day > 31:
            raise ValueError("Day must be between 1 and 31")

        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency is 3-letter ISO code."""
        if not re.match(r"^[A-Z]{3}$", v.upper()):
            raise ValueError("Currency must be 3-letter ISO code (e.g., USD, EUR, GBP)")
        return v.upper()


class ConsolidatedStatementUpdate(BaseModel):
    """Schema for updating a consolidated statement (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    company_name: str | None = Field(None, min_length=1, max_length=255)
    start_period: str | None = None
    end_period: str | None = None
    currency: str | None = Field(None, min_length=3, max_length=3)
    period_count: int | None = Field(None, ge=0)
    total_line_items: int | None = Field(None, ge=0)
    notes: str | None = None

    @field_validator("start_period", "end_period")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date format if provided."""
        if v is None:
            return v

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")

        parts = v.split("-")
        _year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")

        if day < 1 or day > 31:
            raise ValueError("Day must be between 1 and 31")

        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency if provided."""
        if v is None:
            return v

        if not re.match(r"^[A-Z]{3}$", v.upper()):
            raise ValueError("Currency must be 3-letter ISO code")
        return v.upper()


class ConsolidatedStatementSchema(TimestampSchema):
    """Schema for consolidated statement responses."""

    id: int
    name: str
    description: str | None
    company_name: str
    start_period: str
    end_period: str
    currency: str
    period_count: int
    total_line_items: int
    notes: str | None

    model_config = {"from_attributes": True}


class PeriodComparisonCreate(BaseModel):
    """Schema for creating a period comparison."""

    consolidated_statement_id: int = Field(..., gt=0, description="Consolidated statement ID")
    line_item_name: str = Field(..., min_length=1, max_length=255, description="Line item name")
    current_period: str = Field(
        ..., min_length=1, max_length=50, description="Current period label"
    )
    previous_period: str = Field(
        ..., min_length=1, max_length=50, description="Previous period label"
    )
    current_value: Decimal = Field(..., description="Current period value")
    previous_value: Decimal = Field(..., description="Previous period value")
    change_amount: Decimal = Field(..., description="Absolute change")
    change_percentage: Decimal = Field(..., description="Percentage change")
    is_favorable: bool | None = Field(None, description="Whether change is favorable")
    notes: str | None = Field(None, description="Optional notes")


class PeriodComparisonSchema(TimestampSchema):
    """Schema for period comparison responses."""

    id: int
    consolidated_statement_id: int
    line_item_name: str
    current_period: str
    previous_period: str
    current_value: Decimal
    previous_value: Decimal
    change_amount: Decimal
    change_percentage: Decimal
    is_favorable: bool | None
    notes: str | None

    model_config = {"from_attributes": True}


class ConsolidatedStatementWithComparisons(ConsolidatedStatementSchema):
    """Consolidated statement with nested period comparisons."""

    period_comparisons: list[PeriodComparisonSchema] = Field(
        default_factory=list, description="Period-over-period comparisons"
    )

    model_config = {"from_attributes": True}
