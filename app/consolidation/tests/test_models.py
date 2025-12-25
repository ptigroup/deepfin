"""Tests for consolidation models and schemas."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.consolidation.models import ConsolidatedStatement, PeriodComparison
from app.consolidation.schemas import (
    ConsolidatedStatementCreate,
    ConsolidatedStatementSchema,
    ConsolidatedStatementUpdate,
    ConsolidatedStatementWithComparisons,
    PeriodComparisonCreate,
    PeriodComparisonSchema,
)


class TestConsolidatedStatementModel:
    """Tests for ConsolidatedStatement model."""

    def test_consolidated_statement_creation(self):
        """Test creating a consolidated statement."""
        now = datetime.now(UTC)
        statement = ConsolidatedStatement(
            name="Q1-Q4 2024 Consolidated",
            company_name="Acme Corp",
            start_period="2024-01-01",
            end_period="2024-12-31",
            currency="USD",
            period_count=4,
            total_line_items=120,
        )
        statement.created_at = now
        statement.updated_at = now

        assert statement.name == "Q1-Q4 2024 Consolidated"
        assert statement.company_name == "Acme Corp"
        assert statement.period_count == 4
        assert statement.currency == "USD"

    def test_consolidated_statement_with_optional_fields(self):
        """Test consolidated statement with description and notes."""
        now = datetime.now(UTC)
        statement = ConsolidatedStatement(
            name="Annual Consolidation",
            description="Full year financial consolidation",
            company_name="Test Inc",
            start_period="2024-01-01",
            end_period="2024-12-31",
            notes="Includes all quarterly reports",
        )
        statement.created_at = now
        statement.updated_at = now

        assert statement.description == "Full year financial consolidation"
        assert statement.notes == "Includes all quarterly reports"

    def test_consolidated_statement_repr(self):
        """Test string representation of consolidated statement."""
        now = datetime.now(UTC)
        statement = ConsolidatedStatement(
            id=1,
            name="Test Consolidation",
            company_name="Test Corp",
            start_period="2024-01-01",
            end_period="2024-12-31",
            period_count=2,
        )
        statement.created_at = now
        statement.updated_at = now

        assert "ConsolidatedStatement" in repr(statement)
        assert "Test Consolidation" in repr(statement)
        assert "Test Corp" in repr(statement)


class TestPeriodComparisonModel:
    """Tests for PeriodComparison model."""

    def test_period_comparison_creation(self):
        """Test creating a period comparison."""
        now = datetime.now(UTC)
        comparison = PeriodComparison(
            consolidated_statement_id=1,
            line_item_name="Total Revenue",
            current_period="2024 Q4",
            previous_period="2024 Q3",
            current_value=Decimal("1000000.00"),
            previous_value=Decimal("950000.00"),
            change_amount=Decimal("50000.00"),
            change_percentage=Decimal("5.26"),
            is_favorable=True,
        )
        comparison.created_at = now
        comparison.updated_at = now

        assert comparison.line_item_name == "Total Revenue"
        assert comparison.current_value == Decimal("1000000.00")
        assert comparison.change_percentage == Decimal("5.26")
        assert comparison.is_favorable is True

    def test_period_comparison_with_notes(self):
        """Test period comparison with optional notes."""
        now = datetime.now(UTC)
        comparison = PeriodComparison(
            consolidated_statement_id=1,
            line_item_name="Operating Expenses",
            current_period="2024 Q4",
            previous_period="2024 Q3",
            current_value=Decimal("500000.00"),
            previous_value=Decimal("600000.00"),
            change_amount=Decimal("-100000.00"),
            change_percentage=Decimal("-16.67"),
            is_favorable=True,
            notes="Cost reduction initiative successful",
        )
        comparison.created_at = now
        comparison.updated_at = now

        assert comparison.notes == "Cost reduction initiative successful"

    def test_period_comparison_repr(self):
        """Test string representation of period comparison."""
        now = datetime.now(UTC)
        comparison = PeriodComparison(
            id=1,
            consolidated_statement_id=1,
            line_item_name="Revenue",
            current_period="Q4",
            previous_period="Q3",
            current_value=Decimal("1000"),
            previous_value=Decimal("900"),
            change_amount=Decimal("100"),
            change_percentage=Decimal("11.11"),
        )
        comparison.created_at = now
        comparison.updated_at = now

        assert "PeriodComparison" in repr(comparison)
        assert "Revenue" in repr(comparison)


class TestConsolidatedStatementSchema:
    """Tests for ConsolidatedStatement Pydantic schemas."""

    def test_consolidated_statement_create_valid(self):
        """Test creating valid consolidated statement schema."""
        data = {
            "name": "2024 Annual Consolidation",
            "company_name": "Acme Corp",
            "start_period": "2024-01-01",
            "end_period": "2024-12-31",
            "currency": "USD",
            "period_count": 4,
            "total_line_items": 100,
        }

        schema = ConsolidatedStatementCreate(**data)

        assert schema.name == "2024 Annual Consolidation"
        assert schema.currency == "USD"
        assert schema.period_count == 4

    def test_consolidated_statement_create_invalid_date_format(self):
        """Test validation fails for invalid date format."""
        data = {
            "name": "Test",
            "company_name": "Test Corp",
            "start_period": "2024/01/01",  # Invalid format
            "end_period": "2024-12-31",
        }

        with pytest.raises(ValidationError) as exc_info:
            ConsolidatedStatementCreate(**data)

        assert "YYYY-MM-DD" in str(exc_info.value)

    def test_consolidated_statement_create_invalid_month(self):
        """Test validation fails for invalid month."""
        data = {
            "name": "Test",
            "company_name": "Test Corp",
            "start_period": "2024-13-01",  # Invalid month
            "end_period": "2024-12-31",
        }

        with pytest.raises(ValidationError) as exc_info:
            ConsolidatedStatementCreate(**data)

        assert "Month must be between 1 and 12" in str(exc_info.value)

    def test_consolidated_statement_create_invalid_day(self):
        """Test validation fails for invalid day."""
        data = {
            "name": "Test",
            "company_name": "Test Corp",
            "start_period": "2024-01-32",  # Invalid day
            "end_period": "2024-12-31",
        }

        with pytest.raises(ValidationError) as exc_info:
            ConsolidatedStatementCreate(**data)

        assert "Day must be between 1 and 31" in str(exc_info.value)

    def test_consolidated_statement_create_invalid_currency(self):
        """Test validation fails for invalid currency code."""
        data = {
            "name": "Test",
            "company_name": "Test Corp",
            "start_period": "2024-01-01",
            "end_period": "2024-12-31",
            "currency": "US",  # Must be 3 letters
        }

        with pytest.raises(ValidationError) as exc_info:
            ConsolidatedStatementCreate(**data)

        assert "at least 3 characters" in str(exc_info.value)

    def test_consolidated_statement_schema_from_model(self):
        """Test creating schema from SQLAlchemy model."""
        now = datetime.now(UTC)
        model = ConsolidatedStatement(
            id=1,
            name="Test Consolidation",
            company_name="Test Corp",
            start_period="2024-01-01",
            end_period="2024-12-31",
            currency="USD",
            period_count=2,
            total_line_items=50,
        )
        model.created_at = now
        model.updated_at = now

        schema = ConsolidatedStatementSchema.model_validate(model)

        assert schema.id == 1
        assert schema.name == "Test Consolidation"
        assert schema.company_name == "Test Corp"

    def test_consolidated_statement_update_partial(self):
        """Test partial update schema."""
        data = {
            "name": "Updated Name",
            "period_count": 5,
        }

        schema = ConsolidatedStatementUpdate(**data)

        assert schema.name == "Updated Name"
        assert schema.period_count == 5
        assert schema.company_name is None  # Not updated


class TestPeriodComparisonSchema:
    """Tests for PeriodComparison Pydantic schemas."""

    def test_period_comparison_create_valid(self):
        """Test creating valid period comparison schema."""
        data = {
            "consolidated_statement_id": 1,
            "line_item_name": "Revenue",
            "current_period": "2024 Q4",
            "previous_period": "2024 Q3",
            "current_value": Decimal("1000000.00"),
            "previous_value": Decimal("950000.00"),
            "change_amount": Decimal("50000.00"),
            "change_percentage": Decimal("5.26"),
            "is_favorable": True,
        }

        schema = PeriodComparisonCreate(**data)

        assert schema.line_item_name == "Revenue"
        assert schema.current_value == Decimal("1000000.00")
        assert schema.is_favorable is True

    def test_period_comparison_schema_from_model(self):
        """Test creating schema from SQLAlchemy model."""
        now = datetime.now(UTC)
        model = PeriodComparison(
            id=1,
            consolidated_statement_id=1,
            line_item_name="Revenue",
            current_period="Q4",
            previous_period="Q3",
            current_value=Decimal("1000"),
            previous_value=Decimal("900"),
            change_amount=Decimal("100"),
            change_percentage=Decimal("11.11"),
        )
        model.created_at = now
        model.updated_at = now

        schema = PeriodComparisonSchema.model_validate(model)

        assert schema.id == 1
        assert schema.line_item_name == "Revenue"
        assert schema.change_percentage == Decimal("11.11")


class TestConsolidatedStatementWithComparisons:
    """Test nested schema with comparisons."""

    def test_statement_with_comparisons(self):
        """Test consolidated statement with nested comparisons."""
        now = datetime.now(UTC)

        # Create statement model
        statement = ConsolidatedStatement(
            id=1,
            name="Test Consolidation",
            company_name="Test Corp",
            start_period="2024-01-01",
            end_period="2024-12-31",
            currency="USD",
            period_count=2,
            total_line_items=10,
        )
        statement.created_at = now
        statement.updated_at = now

        # Create comparison models
        comparison1 = PeriodComparison(
            id=1,
            consolidated_statement_id=1,
            line_item_name="Revenue",
            current_period="Q4",
            previous_period="Q3",
            current_value=Decimal("1000"),
            previous_value=Decimal("900"),
            change_amount=Decimal("100"),
            change_percentage=Decimal("11.11"),
        )
        comparison1.created_at = now
        comparison1.updated_at = now

        comparison2 = PeriodComparison(
            id=2,
            consolidated_statement_id=1,
            line_item_name="Expenses",
            current_period="Q4",
            previous_period="Q3",
            current_value=Decimal("500"),
            previous_value=Decimal("600"),
            change_amount=Decimal("-100"),
            change_percentage=Decimal("-16.67"),
        )
        comparison2.created_at = now
        comparison2.updated_at = now

        # Add comparisons to statement
        statement.period_comparisons = [comparison1, comparison2]

        # Validate with nested schema
        schema = ConsolidatedStatementWithComparisons.model_validate(statement)

        assert schema.id == 1
        assert schema.name == "Test Consolidation"
        assert len(schema.period_comparisons) == 2
        assert schema.period_comparisons[0].line_item_name == "Revenue"
        assert schema.period_comparisons[1].line_item_name == "Expenses"
