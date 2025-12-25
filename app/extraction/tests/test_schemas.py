"""Tests for extraction schemas and validation."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.extraction.models import ExtractionStatus, StatementType
from app.extraction.schemas import (
    ExtractedLineItemCreate,
    ExtractedStatementCreate,
    ExtractionJobCreate,
    ExtractionJobUpdate,
)


class TestExtractionJobSchemas:
    """Tests for ExtractionJob schemas."""

    def test_extraction_job_create_valid(self):
        """Test creating extraction job with valid data."""
        data = {
            "file_path": "/path/to/statement.pdf",
            "file_name": "statement.pdf",
            "file_hash": "a" * 64,
        }
        schema = ExtractionJobCreate(**data)

        assert schema.file_path == "/path/to/statement.pdf"
        assert schema.file_name == "statement.pdf"
        assert schema.file_hash == "a" * 64

    def test_extraction_job_create_invalid_hash(self):
        """Test extraction job with invalid hash format."""
        data = {
            "file_path": "/path/to/statement.pdf",
            "file_name": "statement.pdf",
            "file_hash": "invalid_hash",  # Not 64 characters
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractionJobCreate(**data)

        # Should fail due to length validation (64 characters required)
        assert "64" in str(exc_info.value) or "string_too_short" in str(exc_info.value).lower()

    def test_extraction_job_create_invalid_extension(self):
        """Test extraction job with non-PDF file."""
        data = {
            "file_path": "/path/to/document.xlsx",
            "file_name": "document.xlsx",
            "file_hash": "a" * 64,
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractionJobCreate(**data)

        assert "pdf" in str(exc_info.value).lower()

    def test_extraction_job_update(self):
        """Test extraction job update schema."""
        data = {
            "status": ExtractionStatus.COMPLETED,
            "statement_type": StatementType.INCOME_STATEMENT,
            "confidence": Decimal("0.95"),
            "processing_time": Decimal("3.5"),
        }
        schema = ExtractionJobUpdate(**data)

        assert schema.status == ExtractionStatus.COMPLETED
        assert schema.confidence == Decimal("0.95")


class TestExtractedStatementSchemas:
    """Tests for ExtractedStatement schemas."""

    def test_extracted_statement_create_valid(self):
        """Test creating extracted statement with valid data."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.BALANCE_SHEET,
            "company_name": "Test Corp",
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
            "currency": "USD",
        }
        schema = ExtractedStatementCreate(**data)

        assert schema.company_name == "Test Corp"
        assert schema.period_start == "2024-01-01"
        assert schema.fiscal_year == 2024

    def test_extracted_statement_create_invalid_date_format(self):
        """Test extracted statement with invalid date format."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.INCOME_STATEMENT,
            "company_name": "Test Corp",
            "period_start": "01/01/2024",  # Wrong format
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
        }

        with pytest.raises(ValidationError):
            ExtractedStatementCreate(**data)

    def test_extracted_statement_create_invalid_month(self):
        """Test extracted statement with invalid month."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.INCOME_STATEMENT,
            "company_name": "Test Corp",
            "period_start": "2024-13-01",  # Invalid month
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedStatementCreate(**data)

        # Error message should indicate invalid date or value
        assert (
            "invalid" in str(exc_info.value).lower() or "value error" in str(exc_info.value).lower()
        )

    def test_extracted_statement_create_invalid_day(self):
        """Test extracted statement with invalid day."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.INCOME_STATEMENT,
            "company_name": "Test Corp",
            "period_start": "2024-02-30",  # February doesn't have 30 days
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
        }

        with pytest.raises(ValidationError):
            ExtractedStatementCreate(**data)

    def test_extracted_statement_create_period_validation(self):
        """Test extracted statement with period_end before period_start."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.INCOME_STATEMENT,
            "company_name": "Test Corp",
            "period_start": "2024-12-31",
            "period_end": "2024-01-01",  # Before start
            "fiscal_year": 2024,
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedStatementCreate(**data)

        assert "after" in str(exc_info.value).lower()

    def test_extracted_statement_create_currency_uppercase(self):
        """Test currency code is converted to uppercase."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.BALANCE_SHEET,
            "company_name": "Test Corp",
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
            "currency": "eur",  # Lowercase
        }
        schema = ExtractedStatementCreate(**data)

        assert schema.currency == "EUR"

    def test_extracted_statement_create_company_name_trimmed(self):
        """Test company name is trimmed of whitespace."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.INCOME_STATEMENT,
            "company_name": "  Test Corp  ",  # Extra whitespace
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
        }
        schema = ExtractedStatementCreate(**data)

        assert schema.company_name == "Test Corp"

    def test_extracted_statement_create_empty_company_name(self):
        """Test extracted statement with empty company name."""
        data = {
            "extraction_job_id": 1,
            "statement_type": StatementType.INCOME_STATEMENT,
            "company_name": "   ",  # Only whitespace
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
            "fiscal_year": 2024,
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedStatementCreate(**data)

        assert "empty" in str(exc_info.value).lower()


class TestExtractedLineItemSchemas:
    """Tests for ExtractedLineItem schemas."""

    def test_extracted_line_item_create_valid(self):
        """Test creating extracted line item with valid data."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "Total Revenue",
            "value": Decimal("1000000.00"),
            "order": 1,
        }
        schema = ExtractedLineItemCreate(**data)

        assert schema.line_item_name == "Total Revenue"
        assert schema.value == Decimal("1000000.00")
        assert schema.indent_level == 0  # Default

    def test_extracted_line_item_create_with_hierarchy(self):
        """Test line item with hierarchical structure."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "Product Revenue",
            "value": Decimal("750000.00"),
            "indent_level": 1,
            "order": 2,
            "parent_id": 1,
            "section": "Revenue",
        }
        schema = ExtractedLineItemCreate(**data)

        assert schema.indent_level == 1
        assert schema.parent_id == 1
        assert schema.section == "Revenue"

    def test_extracted_line_item_create_header_validation(self):
        """Test header validation rules."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "Assets Section",
            "value": Decimal("0.00"),
            "indent_level": 8,  # Too high for header
            "order": 1,
            "is_header": True,
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedLineItemCreate(**data)

        assert "indent" in str(exc_info.value).lower()

    def test_extracted_line_item_create_calculated_without_formula(self):
        """Test calculated item without formula raises error."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "Total",
            "value": Decimal("1000.00"),
            "order": 1,
            "is_calculated": True,
            # Missing formula
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedLineItemCreate(**data)

        assert "formula" in str(exc_info.value).lower()

    def test_extracted_line_item_create_with_formula(self):
        """Test line item with formula."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "Net Income",
            "value": Decimal("500000.00"),
            "order": 10,
            "is_calculated": True,
            "formula": "Revenue - Expenses",
        }
        schema = ExtractedLineItemCreate(**data)

        assert schema.is_calculated is True
        assert schema.formula == "Revenue - Expenses"

    def test_extracted_line_item_create_value_precision(self):
        """Test value precision validation."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "Test",
            "value": Decimal("1000.123456"),  # More than 4 decimal places
            "order": 1,
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedLineItemCreate(**data)

        assert "precision" in str(exc_info.value).lower()

    def test_extracted_line_item_create_name_trimmed(self):
        """Test line item name is trimmed."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "  Revenue  ",
            "value": Decimal("1000.00"),
            "order": 1,
        }
        schema = ExtractedLineItemCreate(**data)

        assert schema.line_item_name == "Revenue"

    def test_extracted_line_item_create_empty_name(self):
        """Test line item with empty name fails validation."""
        data = {
            "extracted_statement_id": 1,
            "line_item_name": "   ",  # Only whitespace
            "value": Decimal("1000.00"),
            "order": 1,
        }

        with pytest.raises(ValidationError):
            ExtractedLineItemCreate(**data)

    def test_extracted_line_item_create_indent_range(self):
        """Test indent level range validation."""
        # Valid minimum
        data_min = {
            "extracted_statement_id": 1,
            "line_item_name": "Level 0",
            "value": Decimal("1000.00"),
            "indent_level": 0,
            "order": 1,
        }
        schema_min = ExtractedLineItemCreate(**data_min)
        assert schema_min.indent_level == 0

        # Valid maximum
        data_max = {
            "extracted_statement_id": 1,
            "line_item_name": "Level 10",
            "value": Decimal("1000.00"),
            "indent_level": 10,
            "order": 1,
        }
        schema_max = ExtractedLineItemCreate(**data_max)
        assert schema_max.indent_level == 10

        # Invalid (too high)
        data_invalid = {
            "extracted_statement_id": 1,
            "line_item_name": "Level 11",
            "value": Decimal("1000.00"),
            "indent_level": 11,
            "order": 1,
        }
        with pytest.raises(ValidationError):
            ExtractedLineItemCreate(**data_invalid)
