"""Tests for consolidation service."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.consolidation.models import ConsolidatedStatement
from app.consolidation.schemas import (
    ConsolidatedStatementCreate,
    PeriodComparisonCreate,
)
from app.consolidation.service import ConsolidationService, ConsolidationServiceError


class TestConsolidationService:
    """Test consolidation service operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock(spec=AsyncSession)
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create consolidation service instance."""
        return ConsolidationService(mock_db)

    @pytest.fixture
    def sample_statement_data(self):
        """Sample consolidated statement data."""
        return ConsolidatedStatementCreate(
            name="Q1-Q4 2024 Consolidated",
            company_name="Acme Corp",
            start_period="2024-01-01",
            end_period="2024-12-31",
            currency="USD",
            period_count=4,
            total_line_items=120,
            description="Annual consolidation for 2024",
        )

    @pytest.fixture
    def sample_statement(self):
        """Sample consolidated statement model."""
        stmt = MagicMock(spec=ConsolidatedStatement)
        stmt.id = 1
        stmt.name = "Q1-Q4 2024 Consolidated"
        stmt.company_name = "Acme Corp"
        stmt.start_period = "2024-01-01"
        stmt.end_period = "2024-12-31"
        stmt.currency = "USD"
        stmt.period_count = 4
        stmt.total_line_items = 120
        stmt.description = "Annual consolidation for 2024"
        stmt.period_comparisons = []
        return stmt

    @pytest.mark.asyncio
    async def test_create_consolidated_statement(self, service, sample_statement_data, mock_db):
        """Test creating consolidated statement."""
        await service.create_consolidated_statement(sample_statement_data)

        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_create_consolidated_statement_minimal(self, service, mock_db):
        """Test creating statement with minimal required fields."""
        statement_data = ConsolidatedStatementCreate(
            name="Minimal Test",
            company_name="Test Corp",
            start_period="2024-01-01",
            end_period="2024-03-31",
        )

        await service.create_consolidated_statement(statement_data)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_consolidated_statement(self, service, sample_statement, mock_db):
        """Test retrieving consolidated statement by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_statement
        mock_db.execute.return_value = mock_result

        statement = await service.get_consolidated_statement(1)

        assert statement is not None
        assert statement.id == 1
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_consolidated_statement_not_found(self, service, mock_db):
        """Test retrieving non-existent statement returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        statement = await service.get_consolidated_statement(99999)

        assert statement is None

    @pytest.mark.asyncio
    async def test_get_consolidated_statement_with_comparisons(
        self, service, sample_statement, mock_db
    ):
        """Test retrieving statement with period comparisons."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_statement
        mock_db.execute.return_value = mock_result

        statement = await service.get_consolidated_statement(1, include_comparisons=True)

        assert statement is not None
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_get_consolidated_statements(self, service, mock_db):
        """Test listing consolidated statements."""
        mock_statements = [
            MagicMock(id=1, company_name="Acme Corp"),
            MagicMock(id=2, company_name="Beta Corp"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_statements
        mock_db.execute.return_value = mock_result

        statements = await service.get_consolidated_statements()

        assert len(statements) == 2
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_consolidated_statements_filter_by_company(self, service, mock_db):
        """Test filtering statements by company name."""
        mock_statements = [MagicMock(id=1, company_name="Acme Corp")]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_statements
        mock_db.execute.return_value = mock_result

        statements = await service.get_consolidated_statements(company_name="Acme Corp")

        assert len(statements) == 1
        assert all(s.company_name == "Acme Corp" for s in statements)

    @pytest.mark.asyncio
    async def test_get_consolidated_statements_pagination(self, service, mock_db):
        """Test pagination of consolidated statements."""
        mock_statements = [MagicMock(id=i) for i in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_statements
        mock_db.execute.return_value = mock_result

        statements = await service.get_consolidated_statements(skip=0, limit=5)

        assert len(statements) == 5

    @pytest.mark.asyncio
    async def test_delete_consolidated_statement(self, service, sample_statement, mock_db):
        """Test deleting consolidated statement."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_statement
        mock_db.execute.return_value = mock_result

        deleted = await service.delete_consolidated_statement(1)

        assert deleted is True
        assert mock_db.delete.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_consolidated_statement_not_found(self, service, mock_db):
        """Test deleting non-existent statement returns False."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        deleted = await service.delete_consolidated_statement(99999)

        assert deleted is False

    @pytest.mark.asyncio
    async def test_add_period_comparison(self, service, sample_statement, mock_db):
        """Test adding period comparison."""
        # Mock statement exists
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = sample_statement
        mock_db.execute.return_value = mock_get_result

        comparison_data = PeriodComparisonCreate(
            consolidated_statement_id=1,
            line_item_name="Total Revenue",
            current_period="Q4 2024",
            previous_period="Q3 2024",
            current_value=Decimal("500000.00"),
            previous_value=Decimal("450000.00"),
            change_amount=Decimal("50000.00"),
            change_percentage=Decimal("11.11"),
            is_favorable=True,
        )

        await service.add_period_comparison(comparison_data)

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_add_period_comparison_statement_not_found(self, service, mock_db):
        """Test adding comparison to non-existent statement fails."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        comparison_data = PeriodComparisonCreate(
            consolidated_statement_id=99999,
            line_item_name="Revenue",
            current_period="Q4 2024",
            previous_period="Q3 2024",
            current_value=Decimal("100000"),
            previous_value=Decimal("90000"),
            change_amount=Decimal("10000"),
            change_percentage=Decimal("11.11"),
        )

        with pytest.raises(ConsolidationServiceError) as exc_info:
            await service.add_period_comparison(comparison_data)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_period_comparisons(self, service, mock_db):
        """Test retrieving period comparisons for statement."""
        mock_comparisons = [
            MagicMock(id=1, line_item_name="Total Revenue"),
            MagicMock(id=2, line_item_name="Operating Expenses"),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_comparisons
        mock_db.execute.return_value = mock_result

        comparisons = await service.get_period_comparisons(1)

        assert len(comparisons) == 2

    @pytest.mark.asyncio
    async def test_get_period_comparisons_empty(self, service, mock_db):
        """Test retrieving comparisons when none exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        comparisons = await service.get_period_comparisons(1)

        assert len(comparisons) == 0

    def test_calculate_change_positive(self, service):
        """Test calculating positive change."""
        current = Decimal("500000.00")
        previous = Decimal("450000.00")

        change_amount, change_percentage = service.calculate_change(current, previous)

        assert change_amount == Decimal("50000.00")
        assert abs(change_percentage - Decimal("11.11")) < Decimal("0.01")

    def test_calculate_change_negative(self, service):
        """Test calculating negative change."""
        current = Decimal("400000.00")
        previous = Decimal("500000.00")

        change_amount, change_percentage = service.calculate_change(current, previous)

        assert change_amount == Decimal("-100000.00")
        assert abs(change_percentage - Decimal("-20.00")) < Decimal("0.01")

    def test_calculate_change_zero_previous(self, service):
        """Test calculating change with zero previous value."""
        current = Decimal("100000.00")
        previous = Decimal("0.00")

        change_amount, change_percentage = service.calculate_change(current, previous)

        assert change_amount == Decimal("100000.00")
        assert change_percentage == Decimal("0")

    def test_calculate_change_no_change(self, service):
        """Test calculating change when values are equal."""
        current = Decimal("500000.00")
        previous = Decimal("500000.00")

        change_amount, change_percentage = service.calculate_change(current, previous)

        assert change_amount == Decimal("0.00")
        assert change_percentage == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_create_comparison_from_values(self, service, sample_statement, mock_db):
        """Test creating comparison with automatic change calculation."""
        # Mock statement exists
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = sample_statement
        mock_db.execute.return_value = mock_get_result

        await service.create_comparison_from_values(
            statement_id=1,
            line_item_name="Net Income",
            current_period="Q4 2024",
            previous_period="Q3 2024",
            current_value=Decimal("150000.00"),
            previous_value=Decimal("120000.00"),
            is_favorable=True,
            notes="Strong quarter",
        )

        assert mock_db.add.called
        assert mock_db.commit.called
