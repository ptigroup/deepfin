"""Consolidation service for multi-period financial data aggregation."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.consolidation.models import ConsolidatedStatement, PeriodComparison
from app.consolidation.schemas import (
    ConsolidatedStatementCreate,
    PeriodComparisonCreate,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConsolidationServiceError(Exception):
    """Exception raised by consolidation service."""

    pass


class ConsolidationService:
    """Service for consolidating financial data across periods.

    Handles:
    - Creating and managing consolidated statements
    - Calculating period-over-period changes
    - Managing period comparisons
    - Data aggregation across multiple periods
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize consolidation service.

        Args:
            db_session: Async database session
        """
        self.db = db_session

    async def create_consolidated_statement(
        self,
        statement_data: ConsolidatedStatementCreate,
    ) -> ConsolidatedStatement:
        """Create a new consolidated statement.

        Args:
            statement_data: Consolidated statement creation data

        Returns:
            Created consolidated statement

        Raises:
            ConsolidationServiceError: If creation fails
        """
        try:
            statement = ConsolidatedStatement(**statement_data.model_dump())
            self.db.add(statement)
            await self.db.commit()
            await self.db.refresh(statement)

            logger.info(
                "Created consolidated statement",
                extra={"statement_id": statement.id, "name": statement.name},
            )

            return statement
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to create consolidated statement",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise ConsolidationServiceError(
                f"Failed to create consolidated statement: {str(e)}"
            ) from e

    async def get_consolidated_statement(
        self,
        statement_id: int,
        include_comparisons: bool = False,
    ) -> ConsolidatedStatement | None:
        """Get consolidated statement by ID.

        Args:
            statement_id: Statement ID
            include_comparisons: Whether to include period comparisons

        Returns:
            Consolidated statement or None if not found
        """
        stmt = select(ConsolidatedStatement).where(ConsolidatedStatement.id == statement_id)
        result = await self.db.execute(stmt)
        statement = result.scalar_one_or_none()

        if statement and include_comparisons:
            # Eagerly load comparisons
            await self.db.refresh(statement, ["period_comparisons"])

        return statement

    async def get_consolidated_statements(
        self,
        company_name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ConsolidatedStatement]:
        """Get list of consolidated statements.

        Args:
            company_name: Filter by company name
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of consolidated statements
        """
        stmt = select(ConsolidatedStatement)

        if company_name:
            stmt = stmt.where(ConsolidatedStatement.company_name == company_name)

        stmt = stmt.offset(skip).limit(limit).order_by(ConsolidatedStatement.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_consolidated_statement(self, statement_id: int) -> bool:
        """Delete consolidated statement and related comparisons.

        Args:
            statement_id: Statement ID to delete

        Returns:
            True if deleted, False if not found
        """
        statement = await self.get_consolidated_statement(statement_id)
        if not statement:
            return False

        await self.db.delete(statement)
        await self.db.commit()

        logger.info(
            "Deleted consolidated statement",
            extra={"statement_id": statement_id},
        )

        return True

    async def add_period_comparison(
        self,
        comparison_data: PeriodComparisonCreate,
    ) -> PeriodComparison:
        """Add period comparison to consolidated statement.

        Args:
            comparison_data: Period comparison creation data

        Returns:
            Created period comparison

        Raises:
            ConsolidationServiceError: If creation fails or statement not found
        """
        # Verify statement exists
        statement = await self.get_consolidated_statement(comparison_data.consolidated_statement_id)
        if not statement:
            raise ConsolidationServiceError(
                f"Consolidated statement {comparison_data.consolidated_statement_id} not found"
            )

        try:
            comparison = PeriodComparison(**comparison_data.model_dump())
            self.db.add(comparison)
            await self.db.commit()
            await self.db.refresh(comparison)

            logger.info(
                "Added period comparison",
                extra={
                    "comparison_id": comparison.id,
                    "statement_id": comparison.consolidated_statement_id,
                },
            )

            return comparison
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to add period comparison",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise ConsolidationServiceError(f"Failed to add period comparison: {str(e)}") from e

    async def get_period_comparisons(
        self,
        statement_id: int,
    ) -> list[PeriodComparison]:
        """Get all period comparisons for a consolidated statement.

        Args:
            statement_id: Consolidated statement ID

        Returns:
            List of period comparisons
        """
        stmt = (
            select(PeriodComparison)
            .where(PeriodComparison.consolidated_statement_id == statement_id)
            .order_by(PeriodComparison.line_item_name)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def calculate_change(
        self,
        current_value: Decimal,
        previous_value: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calculate change amount and percentage.

        Args:
            current_value: Current period value
            previous_value: Previous period value

        Returns:
            Tuple of (change_amount, change_percentage)
        """
        change_amount = current_value - previous_value

        if previous_value == 0:
            # Avoid division by zero
            change_percentage = Decimal("0")
        else:
            change_percentage = (change_amount / previous_value) * Decimal("100")

        return change_amount, change_percentage

    async def create_comparison_from_values(
        self,
        statement_id: int,
        line_item_name: str,
        current_period: str,
        previous_period: str,
        current_value: Decimal,
        previous_value: Decimal,
        is_favorable: bool | None = None,
        notes: str | None = None,
    ) -> PeriodComparison:
        """Create period comparison with automatic change calculation.

        Args:
            statement_id: Consolidated statement ID
            line_item_name: Line item name
            current_period: Current period label
            previous_period: Previous period label
            current_value: Current period value
            previous_value: Previous period value
            is_favorable: Whether change is favorable
            notes: Optional notes

        Returns:
            Created period comparison

        Raises:
            ConsolidationServiceError: If creation fails
        """
        # Calculate changes
        change_amount, change_percentage = self.calculate_change(current_value, previous_value)

        # Create comparison
        comparison_data = PeriodComparisonCreate(
            consolidated_statement_id=statement_id,
            line_item_name=line_item_name,
            current_period=current_period,
            previous_period=previous_period,
            current_value=current_value,
            previous_value=previous_value,
            change_amount=change_amount,
            change_percentage=change_percentage,
            is_favorable=is_favorable,
            notes=notes,
        )

        return await self.add_period_comparison(comparison_data)
