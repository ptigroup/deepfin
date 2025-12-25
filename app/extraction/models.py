"""Database models for financial data extraction."""

import enum
from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class ExtractionStatus(str, enum.Enum):
    """Status of an extraction job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StatementType(str, enum.Enum):
    """Type of financial statement."""

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    UNKNOWN = "unknown"


class ExtractionJob(Base, TimestampMixin):
    """Extraction job tracking model.

    Represents a PDF processing job that extracts financial data.
    Tracks the lifecycle of an extraction from upload to completion.

    Attributes:
        id: Primary key
        file_path: Path to the source PDF file
        file_name: Original filename
        file_hash: SHA256 hash of the file for deduplication
        status: Current status of the extraction job
        statement_type: Detected type of financial statement
        confidence: Confidence score for statement type detection (0.0 to 1.0)
        company_name: Extracted company name
        period_start: Extracted period start date (YYYY-MM-DD)
        period_end: Extracted period end date (YYYY-MM-DD)
        fiscal_year: Extracted fiscal year
        currency: Detected currency code
        extracted_text: Raw text extracted from PDF
        error_message: Error message if extraction failed
        processing_time: Time taken to process (seconds)
        extracted_statements: Related extracted statement records
    """

    __tablename__ = "extraction_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus), nullable=False, default=ExtractionStatus.PENDING, index=True
    )
    statement_type: Mapped[StatementType] = mapped_column(
        Enum(StatementType), nullable=True, default=StatementType.UNKNOWN
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=4), nullable=True
    )  # 0.0000 to 1.0000
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    period_start: Mapped[str | None] = mapped_column(String(10), nullable=True)
    period_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    fiscal_year: Mapped[int | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=2), nullable=True
    )

    # Relationships
    extracted_statements: Mapped[list["ExtractedStatement"]] = relationship(
        back_populates="extraction_job", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="confidence_range"),
        CheckConstraint(
            "processing_time IS NULL OR processing_time >= 0", name="processing_time_positive"
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ExtractionJob(id={self.id}, file='{self.file_name}', "
            f"status='{self.status.value}', type='{self.statement_type.value}')>"
        )


class ExtractedStatement(Base, TimestampMixin):
    """Extracted financial statement model.

    Represents intermediate extracted data before validation and conversion
    to permanent Statement records. Supports hierarchical data with sections.

    Attributes:
        id: Primary key
        extraction_job_id: Foreign key to extraction job
        statement_type: Type of financial statement
        company_name: Company name
        period_start: Period start date (YYYY-MM-DD)
        period_end: Period end date (YYYY-MM-DD)
        fiscal_year: Fiscal year
        currency: Currency code
        total_line_items: Count of extracted line items
        has_errors: Whether extraction had validation errors
        validation_errors: JSON text with validation error details
        extraction_metadata: Additional extraction metadata as JSON
        extraction_job: Related extraction job
        line_items: Related extracted line items
    """

    __tablename__ = "extracted_statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_job_id: Mapped[int] = mapped_column(
        ForeignKey("extraction_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    statement_type: Mapped[StatementType] = mapped_column(
        Enum(StatementType), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[str] = mapped_column(String(10), nullable=False)
    period_end: Mapped[str] = mapped_column(String(10), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    total_line_items: Mapped[int] = mapped_column(nullable=False, default=0)
    has_errors: Mapped[bool] = mapped_column(nullable=False, default=False)
    validation_errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    extraction_job: Mapped["ExtractionJob"] = relationship(back_populates="extracted_statements")
    line_items: Mapped[list["ExtractedLineItem"]] = relationship(
        back_populates="extracted_statement",
        cascade="all, delete-orphan",
        order_by="ExtractedLineItem.order",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("length(period_start) = 10", name="extracted_period_start_format"),
        CheckConstraint("length(period_end) = 10", name="extracted_period_end_format"),
        CheckConstraint("length(currency) = 3", name="extracted_currency_length"),
        CheckConstraint("fiscal_year > 1900", name="extracted_fiscal_year_valid"),
        CheckConstraint("total_line_items >= 0", name="extracted_total_line_items_positive"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ExtractedStatement(id={self.id}, type='{self.statement_type.value}', "
            f"company='{self.company_name}', items={self.total_line_items})>"
        )


class ExtractedLineItem(Base, TimestampMixin):
    """Extracted line item model.

    Represents a single extracted line item from a financial statement.
    Includes hierarchical structure, validation rules, and categorization.

    Attributes:
        id: Primary key
        extracted_statement_id: Foreign key to extracted statement
        line_item_name: Name/description of the line item (preserved exactly)
        category: Optional category classification
        value: Numeric value (preserved with high precision)
        indent_level: Indentation level for hierarchy (0-10)
        order: Display order within statement
        parent_id: Optional parent line item for hierarchical structure
        section: Section name (e.g., 'Assets', 'Revenue')
        is_header: Whether this is a section header
        is_total: Whether this is a total/subtotal line
        is_calculated: Whether value is calculated vs. direct entry
        formula: Optional formula for calculated values
        notes: Optional notes or annotations
        validation_warnings: Validation warnings as JSON text
        raw_text: Original raw text from extraction
        extracted_statement: Related extracted statement
        children: Child line items (for hierarchical structure)
        parent: Parent line item (for hierarchical structure)
    """

    __tablename__ = "extracted_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    extracted_statement_id: Mapped[int] = mapped_column(
        ForeignKey("extracted_statements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_item_name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=4), nullable=False)
    indent_level: Mapped[int] = mapped_column(nullable=False, default=0)
    order: Mapped[int] = mapped_column(nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("extracted_line_items.id", ondelete="SET NULL"), nullable=True
    )
    section: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    is_header: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_total: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_calculated: Mapped[bool] = mapped_column(nullable=False, default=False)
    formula: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    extracted_statement: Mapped["ExtractedStatement"] = relationship(back_populates="line_items")
    children: Mapped[list["ExtractedLineItem"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="ExtractedLineItem.parent_id",
    )
    parent: Mapped["ExtractedLineItem | None"] = relationship(
        back_populates="children", remote_side="ExtractedLineItem.id"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("indent_level >= 0 AND indent_level <= 10", name="indent_level_range"),
        CheckConstraint("order >= 0", name="order_non_negative"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ExtractedLineItem(id={self.id}, name='{self.line_item_name[:30]}', "
            f"value={self.value}, indent={self.indent_level})>"
        )
