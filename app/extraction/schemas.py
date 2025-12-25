"""Pydantic schemas for financial data extraction with complex validation."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.extraction.models import ExtractionStatus, StatementType


class ExtractedLineItemCreate(BaseModel):
    """Schema for creating an extracted line item."""

    extracted_statement_id: int = Field(
        ..., gt=0, description="ID of the parent extracted statement"
    )
    line_item_name: str = Field(
        ..., min_length=1, max_length=500, description="Name of the line item"
    )
    category: str | None = Field(None, max_length=100, description="Category classification")
    value: Decimal = Field(..., description="Numeric value")
    indent_level: int = Field(default=0, ge=0, le=10, description="Indentation level (0-10)")
    order: int = Field(..., ge=0, description="Display order")
    parent_id: int | None = Field(None, gt=0, description="Parent line item ID")
    section: str | None = Field(None, max_length=200, description="Section name")
    is_header: bool = Field(default=False, description="Is this a section header")
    is_total: bool = Field(default=False, description="Is this a total line")
    is_calculated: bool = Field(default=False, description="Is value calculated")
    formula: str | None = Field(None, max_length=500, description="Formula for calculated values")
    notes: str | None = Field(None, description="Additional notes")
    raw_text: str | None = Field(None, description="Original raw text")

    @field_validator("line_item_name")
    @classmethod
    def validate_line_item_name(cls, v: str) -> str:
        """Validate line item name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Line item name cannot be empty or whitespace")
        return v.strip()

    @field_validator("value")
    @classmethod
    def validate_value_precision(cls, v: Decimal) -> Decimal:
        """Validate value has reasonable precision (max 4 decimal places)."""
        if v.as_tuple().exponent < -4:
            raise ValueError("Value precision cannot exceed 4 decimal places")
        return v

    @model_validator(mode="after")
    def validate_header_and_total(self):
        """Validate that headers and totals have appropriate properties."""
        # Headers typically don't have values or should be at lower indent levels
        if self.is_header and self.indent_level > 5:
            raise ValueError("Header items should not have indent level > 5")

        # Total lines should have a formula or be calculated (warning only)
        if self.is_total and not self.is_calculated and not self.formula:
            # This is a warning, not an error, so we'll allow it
            pass

        # Calculated items must have a formula
        if self.is_calculated and not self.formula:
            raise ValueError("Calculated items must have a formula")

        return self


class ExtractedLineItemUpdate(BaseModel):
    """Schema for updating an extracted line item."""

    line_item_name: str | None = Field(None, min_length=1, max_length=500)
    category: str | None = Field(None, max_length=100)
    value: Decimal | None = None
    indent_level: int | None = Field(None, ge=0, le=10)
    order: int | None = Field(None, ge=0)
    parent_id: int | None = Field(None, gt=0)
    section: str | None = Field(None, max_length=200)
    is_header: bool | None = None
    is_total: bool | None = None
    is_calculated: bool | None = None
    formula: str | None = Field(None, max_length=500)
    notes: str | None = None


class ExtractedLineItemSchema(BaseModel):
    """Schema for extracted line item response."""

    id: int
    extracted_statement_id: int
    line_item_name: str
    category: str | None
    value: Decimal
    indent_level: int
    order: int
    parent_id: int | None
    section: str | None
    is_header: bool
    is_total: bool
    is_calculated: bool
    formula: str | None
    notes: str | None
    validation_warnings: str | None
    raw_text: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExtractedStatementCreate(BaseModel):
    """Schema for creating an extracted statement."""

    extraction_job_id: int = Field(..., gt=0, description="ID of the extraction job")
    statement_type: StatementType = Field(..., description="Type of financial statement")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    period_start: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Period start (YYYY-MM-DD)"
    )
    period_end: str = Field(
        ..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Period end (YYYY-MM-DD)"
    )
    fiscal_year: int = Field(..., ge=1900, le=2100, description="Fiscal year")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    extraction_metadata: str | None = Field(None, description="Additional metadata as JSON")

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        """Validate company name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Company name cannot be empty or whitespace")
        return v.strip()

    @field_validator("currency")
    @classmethod
    def validate_currency_uppercase(cls, v: str) -> str:
        """Ensure currency code is uppercase."""
        return v.upper()

    @field_validator("period_start", "period_end")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in YYYY-MM-DD format and is valid."""
        try:
            year, month, day = v.split("-")
            _year_int, month_int, day_int = int(year), int(month), int(day)

            if not (1 <= month_int <= 12):
                raise ValueError(f"Invalid month: {month_int}")
            if not (1 <= day_int <= 31):
                raise ValueError(f"Invalid day: {day_int}")

            # Basic day validation (simplified)
            if month_int in [4, 6, 9, 11] and day_int > 30:
                raise ValueError(f"Month {month_int} cannot have {day_int} days")
            if month_int == 2 and day_int > 29:
                raise ValueError("February cannot have more than 29 days")

        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid date format or value: {v}") from e

        return v

    @model_validator(mode="after")
    def validate_period_dates(self):
        """Validate that period_end is after period_start."""
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError("period_end must be after period_start")
        return self


class ExtractedStatementUpdate(BaseModel):
    """Schema for updating an extracted statement."""

    statement_type: StatementType | None = None
    company_name: str | None = Field(None, min_length=1, max_length=255)
    period_start: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    period_end: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    fiscal_year: int | None = Field(None, ge=1900, le=2100)
    currency: str | None = Field(None, min_length=3, max_length=3)
    has_errors: bool | None = None
    validation_errors: str | None = None


class ExtractedStatementSchema(BaseModel):
    """Schema for extracted statement response."""

    id: int
    extraction_job_id: int
    statement_type: StatementType
    company_name: str
    period_start: str
    period_end: str
    fiscal_year: int
    currency: str
    total_line_items: int
    has_errors: bool
    validation_errors: str | None
    extraction_metadata: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExtractedStatementWithLineItems(ExtractedStatementSchema):
    """Schema for extracted statement with line items."""

    line_items: list[ExtractedLineItemSchema] = []

    model_config = {"from_attributes": True}


class ExtractionJobCreate(BaseModel):
    """Schema for creating an extraction job."""

    file_path: str = Field(..., min_length=1, max_length=500, description="Path to source PDF")
    file_name: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash")

    @field_validator("file_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        """Validate hash is hexadecimal."""
        if not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("File hash must be a valid hexadecimal string")
        return v.lower()

    @field_validator("file_name")
    @classmethod
    def validate_file_extension(cls, v: str) -> str:
        """Validate file has .pdf extension."""
        if not v.lower().endswith(".pdf"):
            raise ValueError("File must be a PDF (.pdf extension)")
        return v


class ExtractionJobUpdate(BaseModel):
    """Schema for updating an extraction job."""

    status: ExtractionStatus | None = None
    statement_type: StatementType | None = None
    confidence: Decimal | None = Field(None, ge=0.0, le=1.0)
    company_name: str | None = Field(None, max_length=255)
    period_start: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    period_end: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    fiscal_year: int | None = Field(None, ge=1900, le=2100)
    currency: str | None = Field(None, min_length=3, max_length=3)
    extracted_text: str | None = None
    error_message: str | None = None
    processing_time: Decimal | None = Field(None, ge=0.0)


class ExtractionJobSchema(BaseModel):
    """Schema for extraction job response."""

    id: int
    file_path: str
    file_name: str
    file_hash: str
    status: ExtractionStatus
    statement_type: StatementType
    confidence: Decimal | None
    company_name: str | None
    period_start: str | None
    period_end: str | None
    fiscal_year: int | None
    currency: str | None
    error_message: str | None
    processing_time: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExtractionJobWithStatements(ExtractionJobSchema):
    """Schema for extraction job with extracted statements."""

    extracted_statements: list[ExtractedStatementSchema] = []

    model_config = {"from_attributes": True}
