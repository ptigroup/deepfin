"""Tests for statements models and schemas."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.statements.models import LineItem, Statement, StatementType
from app.statements.schemas import (
    LineItemCreate,
    LineItemSchema,
    LineItemUpdate,
    StatementCreate,
    StatementSchema,
    StatementUpdate,
    StatementWithLineItems,
)


class TestStatementModel:
    """Tests for Statement model."""

    def test_statement_creation(self):
        """Test creating a statement."""
        stmt = Statement(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Acme Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="USD",
            fiscal_year=2024,
        )
        assert stmt.statement_type == StatementType.INCOME_STATEMENT
        assert stmt.company_name == "Acme Corp"
        assert stmt.period_start == "2024-01-01"
        assert stmt.period_end == "2024-12-31"
        assert stmt.currency == "USD"
        assert stmt.fiscal_year == 2024
        assert stmt.extra_metadata is None

    def test_statement_with_metadata(self):
        """Test creating statement with extra_metadata."""
        stmt = Statement(
            statement_type=StatementType.BALANCE_SHEET,
            company_name="Test Inc",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="EUR",
            fiscal_year=2024,
            extra_metadata='{"source": "manual", "version": "1.0"}',
        )
        assert stmt.extra_metadata == '{"source": "manual", "version": "1.0"}'

    def test_statement_repr(self):
        """Test statement string representation."""
        stmt = Statement(
            statement_type=StatementType.CASH_FLOW,
            company_name="Test Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="USD",
            fiscal_year=2024,
        )
        stmt.id = 1
        repr_str = repr(stmt)
        assert "Statement" in repr_str
        assert "id=1" in repr_str
        assert "cash_flow" in repr_str
        assert "Test Corp" in repr_str
        assert "2024-01-01 to 2024-12-31" in repr_str


class TestLineItemModel:
    """Tests for LineItem model."""

    def test_line_item_creation(self):
        """Test creating a line item."""
        item = LineItem(
            statement_id=1,
            line_item_name="Total Revenue",
            category="Revenue",
            value=Decimal("1000000.00"),
            indent_level=0,
            order=1,
        )
        assert item.statement_id == 1
        assert item.line_item_name == "Total Revenue"
        assert item.category == "Revenue"
        assert item.value == Decimal("1000000.00")
        assert item.indent_level == 0
        assert item.order == 1
        assert item.parent_id is None
        assert item.notes is None

    def test_line_item_with_parent(self):
        """Test creating line item with parent."""
        item = LineItem(
            statement_id=1,
            line_item_name="Product Revenue",
            category="Revenue",
            value=Decimal("750000.00"),
            indent_level=1,
            order=2,
            parent_id=1,
        )
        assert item.parent_id == 1
        assert item.indent_level == 1

    def test_line_item_with_notes(self):
        """Test creating line item with notes."""
        item = LineItem(
            statement_id=1,
            line_item_name="Depreciation",
            category="Expenses",
            value=Decimal("50000.00"),
            indent_level=0,
            order=5,
            notes="Straight-line depreciation method",
        )
        assert item.notes == "Straight-line depreciation method"

    def test_line_item_repr(self):
        """Test line item string representation."""
        item = LineItem(
            statement_id=1,
            line_item_name="Total Assets",
            category="Assets",
            value=Decimal("5000000.00"),
            indent_level=0,
            order=1,
        )
        item.id = 10
        repr_str = repr(item)
        assert "LineItem" in repr_str
        assert "id=10" in repr_str
        assert "Total Assets" in repr_str
        assert "5000000.00" in repr_str
        assert "Assets" in repr_str


class TestStatementSchema:
    """Tests for Statement Pydantic schemas."""

    def test_statement_create_valid(self):
        """Test creating a valid statement."""
        stmt = StatementCreate(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Acme Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="USD",
            fiscal_year=2024,
        )
        assert stmt.statement_type == StatementType.INCOME_STATEMENT
        assert stmt.company_name == "Acme Corp"
        assert stmt.period_start == "2024-01-01"
        assert stmt.period_end == "2024-12-31"
        assert stmt.currency == "USD"
        assert stmt.fiscal_year == 2024

    def test_statement_create_invalid_date_format(self):
        """Test creating statement with invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            StatementCreate(
                statement_type=StatementType.INCOME_STATEMENT,
                company_name="Acme Corp",
                period_start="2024/01/01",  # Wrong format
                period_end="2024-12-31",
                currency="USD",
                fiscal_year=2024,
            )
        assert "period_start" in str(exc_info.value)

    def test_statement_create_invalid_month(self):
        """Test creating statement with invalid month."""
        with pytest.raises(ValidationError) as exc_info:
            StatementCreate(
                statement_type=StatementType.INCOME_STATEMENT,
                company_name="Acme Corp",
                period_start="2024-13-01",  # Month 13 doesn't exist
                period_end="2024-12-31",
                currency="USD",
                fiscal_year=2024,
            )
        assert "Month must be between 01 and 12" in str(exc_info.value)

    def test_statement_create_invalid_day(self):
        """Test creating statement with invalid day."""
        with pytest.raises(ValidationError) as exc_info:
            StatementCreate(
                statement_type=StatementType.INCOME_STATEMENT,
                company_name="Acme Corp",
                period_start="2024-01-32",  # Day 32 doesn't exist
                period_end="2024-12-31",
                currency="USD",
                fiscal_year=2024,
            )
        assert "Day must be between 01 and 31" in str(exc_info.value)

    def test_statement_create_invalid_currency(self):
        """Test creating statement with invalid currency."""
        with pytest.raises(ValidationError) as exc_info:
            StatementCreate(
                statement_type=StatementType.INCOME_STATEMENT,
                company_name="Acme Corp",
                period_start="2024-01-01",
                period_end="2024-12-31",
                currency="usd",  # Must be uppercase
                fiscal_year=2024,
            )
        assert "currency" in str(exc_info.value).lower()

    def test_statement_create_invalid_fiscal_year(self):
        """Test creating statement with invalid fiscal year."""
        with pytest.raises(ValidationError) as exc_info:
            StatementCreate(
                statement_type=StatementType.INCOME_STATEMENT,
                company_name="Acme Corp",
                period_start="2024-01-01",
                period_end="2024-12-31",
                currency="USD",
                fiscal_year=1800,  # Too old
            )
        assert "fiscal_year" in str(exc_info.value)

    def test_statement_schema_from_model(self):
        """Test creating schema from model."""
        now = datetime.now(UTC)
        stmt = Statement(
            statement_type=StatementType.BALANCE_SHEET,
            company_name="Test Inc",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="EUR",
            fiscal_year=2024,
        )
        stmt.id = 1
        stmt.created_at = now
        stmt.updated_at = now
        schema = StatementSchema.model_validate(stmt)
        assert schema.id == 1
        assert schema.statement_type == StatementType.BALANCE_SHEET
        assert schema.company_name == "Test Inc"

    def test_statement_update_partial(self):
        """Test updating statement with partial data."""
        update = StatementUpdate(company_name="New Corp Name")
        assert update.company_name == "New Corp Name"
        assert update.currency is None
        assert update.fiscal_year is None


class TestLineItemSchema:
    """Tests for LineItem Pydantic schemas."""

    def test_line_item_create_valid(self):
        """Test creating a valid line item."""
        item = LineItemCreate(
            statement_id=1,
            line_item_name="Total Revenue",
            category="Revenue",
            value=Decimal("1000000.00"),
            indent_level=0,
            order=1,
        )
        assert item.statement_id == 1
        assert item.line_item_name == "Total Revenue"
        assert item.value == Decimal("1000000.00")

    def test_line_item_create_with_parent(self):
        """Test creating line item with parent."""
        item = LineItemCreate(
            statement_id=1,
            line_item_name="Product Revenue",
            category="Revenue",
            value=Decimal("750000.00"),
            indent_level=1,
            order=2,
            parent_id=1,
        )
        assert item.parent_id == 1

    def test_line_item_create_invalid_indent_level(self):
        """Test creating line item with invalid indent level."""
        with pytest.raises(ValidationError) as exc_info:
            LineItemCreate(
                statement_id=1,
                line_item_name="Test",
                value=Decimal("100.00"),
                indent_level=6,  # Max is 5
                order=1,
            )
        assert "indent_level" in str(exc_info.value)

    def test_line_item_create_negative_order(self):
        """Test creating line item with negative order."""
        with pytest.raises(ValidationError) as exc_info:
            LineItemCreate(
                statement_id=1,
                line_item_name="Test",
                value=Decimal("100.00"),
                indent_level=0,
                order=-1,  # Must be >= 0
            )
        assert "order" in str(exc_info.value)

    def test_line_item_create_invalid_decimal_places(self):
        """Test creating line item with too many decimal places."""
        with pytest.raises(ValidationError) as exc_info:
            LineItemCreate(
                statement_id=1,
                line_item_name="Test",
                value=Decimal("100.123"),  # More than 2 decimal places
                indent_level=0,
                order=1,
            )
        assert "value must have at most 2 decimal places" in str(exc_info.value)

    def test_line_item_schema_from_model(self):
        """Test creating schema from model."""
        now = datetime.now(UTC)
        item = LineItem(
            statement_id=1,
            line_item_name="Cash",
            category="Assets",
            value=Decimal("250000.00"),
            indent_level=1,
            order=3,
        )
        item.id = 5
        item.created_at = now
        item.updated_at = now
        schema = LineItemSchema.model_validate(item)
        assert schema.id == 5
        assert schema.line_item_name == "Cash"
        assert schema.value == Decimal("250000.00")

    def test_line_item_update_partial(self):
        """Test updating line item with partial data."""
        update = LineItemUpdate(value=Decimal("2000000.00"))
        assert update.value == Decimal("2000000.00")
        assert update.line_item_name is None
        assert update.category is None


class TestStatementWithLineItems:
    """Tests for nested statement with line items."""

    def test_statement_with_line_items(self):
        """Test statement with nested line items."""
        now = datetime.now(UTC)
        stmt = Statement(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            currency="USD",
            fiscal_year=2024,
        )
        stmt.id = 1
        stmt.created_at = now
        stmt.updated_at = now
        stmt.line_items = [
            LineItem(
                statement_id=1,
                line_item_name="Total Revenue",
                category="Revenue",
                value=Decimal("1000000.00"),
                indent_level=0,
                order=1,
            ),
            LineItem(
                statement_id=1,
                line_item_name="Product Revenue",
                category="Revenue",
                value=Decimal("750000.00"),
                indent_level=1,
                order=2,
            ),
        ]
        for i, item in enumerate(stmt.line_items):
            item.id = i + 1
            item.created_at = now
            item.updated_at = now

        schema = StatementWithLineItems.model_validate(stmt)
        assert schema.id == 1
        assert len(schema.line_items) == 2
        assert schema.line_items[0].line_item_name == "Total Revenue"
        assert schema.line_items[1].indent_level == 1
