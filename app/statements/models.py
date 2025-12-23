"""Database models for financial statements."""

import enum
from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class StatementType(str, enum.Enum):
    """Type of financial statement."""

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"


class Statement(Base, TimestampMixin):
    """Financial statement model.

    Represents a complete financial statement (Income Statement, Balance Sheet,
    or Cash Flow Statement) for a specific period.

    Attributes:
        id: Primary key
        statement_type: Type of statement (income, balance_sheet, cash_flow)
        company_name: Name of the company
        period_start: Start date of the reporting period (YYYY-MM-DD format)
        period_end: End date of the reporting period (YYYY-MM-DD format)
        currency: Currency code (e.g., USD, EUR)
        fiscal_year: Fiscal year for the statement
        metadata: Additional metadata as JSON text
        line_items: Related line items for this statement

    Example:
        statement = Statement(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Acme Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="USD",
            fiscal_year=2024
        )
    """

    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_type: Mapped[StatementType] = mapped_column(
        Enum(StatementType), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    period_start: Mapped[str] = mapped_column(String(10), nullable=False)
    period_end: Mapped[str] = mapped_column(String(10), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    fiscal_year: Mapped[int] = mapped_column(nullable=False, index=True)
    extra_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    line_items: Mapped[list["LineItem"]] = relationship(
        back_populates="statement",
        cascade="all, delete-orphan",
        order_by="LineItem.order",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("length(period_start) = 10", name="period_start_format"),
        CheckConstraint("length(period_end) = 10", name="period_end_format"),
        CheckConstraint("length(currency) = 3", name="currency_code_length"),
        CheckConstraint("fiscal_year > 1900", name="fiscal_year_valid"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Statement(id={self.id}, type='{self.statement_type.value}', "
            f"company='{self.company_name}', period='{self.period_start} to {self.period_end}')>"
        )


class LineItem(Base, TimestampMixin):
    """Line item within a financial statement.

    Represents a single line in a financial statement (e.g., Revenue, Assets,
    Operating Cash Flow). Supports hierarchical structure through parent-child
    relationships.

    Attributes:
        id: Primary key
        statement_id: Foreign key to Statement
        line_item_name: Name of the line item (e.g., "Total Revenue")
        category: Category for grouping (e.g., "Revenue", "Assets")
        value: Numeric value for this line item
        indent_level: Indentation level for hierarchical display (0-5)
        order: Display order within the statement
        parent_id: Optional parent line item for hierarchical structure
        notes: Optional notes or annotations
        statement: Related statement
        children: Child line items (for hierarchical structure)
        parent: Parent line item (for hierarchical structure)

    Example:
        revenue_item = LineItem(
            statement_id=1,
            line_item_name="Total Revenue",
            category="Revenue",
            value=Decimal("1000000.00"),
            indent_level=0,
            order=1
        )
    """

    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_id: Mapped[int] = mapped_column(
        ForeignKey("statements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_item_name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=2), nullable=False)
    indent_level: Mapped[int] = mapped_column(nullable=False, default=0)
    order: Mapped[int] = mapped_column(nullable=False, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("line_items.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    statement: Mapped["Statement"] = relationship(back_populates="line_items")
    children: Mapped[list["LineItem"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="LineItem.parent_id",
    )
    parent: Mapped["LineItem | None"] = relationship(
        back_populates="children",
        remote_side="LineItem.id",
        foreign_keys="LineItem.parent_id",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("indent_level >= 0 AND indent_level <= 5", name="indent_level_range"),
        CheckConstraint("order >= 0", name="order_non_negative"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<LineItem(id={self.id}, name='{self.line_item_name}', "
            f"value={self.value}, category='{self.category}')>"
        )
