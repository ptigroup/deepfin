"""Database models for financial data consolidation.

This module provides models for aggregating multi-period financial data,
enabling period-over-period comparisons and consolidated reporting.
"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models import TimestampMixin


class ConsolidatedStatement(Base, TimestampMixin):
    """Consolidated financial statement aggregating multiple periods.

    Represents a consolidated view of financial statements across multiple
    time periods, enabling trend analysis and period comparisons.

    Attributes:
        id: Primary key
        name: Descriptive name for the consolidation
        description: Optional detailed description
        company_name: Company for consolidated statements
        start_period: Earliest period included (YYYY-MM-DD)
        end_period: Latest period included (YYYY-MM-DD)
        currency: Currency code (ISO 4217)
        period_count: Number of periods included
        total_line_items: Total line items across all periods
        notes: Optional notes about the consolidation
        period_comparisons: Related period comparisons
        created_at: Auto-managed creation timestamp
        updated_at: Auto-managed update timestamp
    """

    __tablename__ = "consolidated_statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_name: Mapped[str] = mapped_column()
    start_period: Mapped[str] = mapped_column()  # YYYY-MM-DD format
    end_period: Mapped[str] = mapped_column()  # YYYY-MM-DD format
    currency: Mapped[str] = mapped_column(default="USD")
    period_count: Mapped[int] = mapped_column(default=0)
    total_line_items: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    period_comparisons: Mapped[list["PeriodComparison"]] = relationship(
        back_populates="consolidated_statement",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of consolidated statement."""
        return (
            f"<ConsolidatedStatement(id={self.id}, name='{self.name}', "
            f"company='{self.company_name}', periods={self.period_count})>"
        )


class PeriodComparison(Base, TimestampMixin):
    """Period-over-period comparison for a specific line item.

    Tracks changes in financial metrics between two periods, including
    absolute and percentage changes.

    Attributes:
        id: Primary key
        consolidated_statement_id: Foreign key to consolidated statement
        line_item_name: Name of the line item being compared
        current_period: Current period label (e.g., "2024 Q4")
        previous_period: Previous period label (e.g., "2024 Q3")
        current_value: Value in current period
        previous_value: Value in previous period
        change_amount: Absolute change (current - previous)
        change_percentage: Percentage change ((current - previous) / previous * 100)
        is_favorable: Whether change is favorable (based on context)
        notes: Optional notes about the comparison
        consolidated_statement: Parent consolidated statement
        created_at: Auto-managed creation timestamp
        updated_at: Auto-managed update timestamp
    """

    __tablename__ = "period_comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    consolidated_statement_id: Mapped[int] = mapped_column(
        ForeignKey("consolidated_statements.id", ondelete="CASCADE")
    )
    line_item_name: Mapped[str] = mapped_column()
    current_period: Mapped[str] = mapped_column()
    previous_period: Mapped[str] = mapped_column()
    current_value: Mapped[Decimal] = mapped_column()
    previous_value: Mapped[Decimal] = mapped_column()
    change_amount: Mapped[Decimal] = mapped_column()
    change_percentage: Mapped[Decimal] = mapped_column()
    is_favorable: Mapped[bool | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    consolidated_statement: Mapped["ConsolidatedStatement"] = relationship(
        back_populates="period_comparisons"
    )

    def __repr__(self) -> str:
        """String representation of period comparison."""
        return (
            f"<PeriodComparison(id={self.id}, item='{self.line_item_name}', "
            f"change={self.change_percentage}%)>"
        )
