"""Tests for extraction models."""

from decimal import Decimal

from app.extraction.models import (
    ExtractedLineItem,
    ExtractedStatement,
    ExtractionJob,
    ExtractionStatus,
    StatementType,
)


class TestExtractionJob:
    """Tests for ExtractionJob model."""

    def test_extraction_job_creation(self):
        """Test creating an extraction job."""
        job = ExtractionJob(
            file_path="/path/to/file.pdf",
            file_name="statement.pdf",
            file_hash="a" * 64,
            status=ExtractionStatus.PENDING,
        )

        assert job.file_path == "/path/to/file.pdf"
        assert job.file_name == "statement.pdf"
        assert job.file_hash == "a" * 64
        assert job.status == ExtractionStatus.PENDING
        assert job.statement_type is None or job.statement_type == StatementType.UNKNOWN

    def test_extraction_job_with_metadata(self):
        """Test extraction job with extracted metadata."""
        job = ExtractionJob(
            file_path="/path/to/file.pdf",
            file_name="statement.pdf",
            file_hash="b" * 64,
            status=ExtractionStatus.COMPLETED,
            statement_type=StatementType.INCOME_STATEMENT,
            confidence=Decimal("0.95"),
            company_name="Test Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="USD",
            processing_time=Decimal("5.25"),
        )

        assert job.status == ExtractionStatus.COMPLETED
        assert job.statement_type == StatementType.INCOME_STATEMENT
        assert job.confidence == Decimal("0.95")
        assert job.company_name == "Test Corp"
        assert job.processing_time == Decimal("5.25")

    def test_extraction_job_repr(self):
        """Test string representation of extraction job."""
        job = ExtractionJob(
            file_path="/path/to/file.pdf",
            file_name="statement.pdf",
            file_hash="c" * 64,
            status=ExtractionStatus.PROCESSING,
            statement_type=StatementType.BALANCE_SHEET,
        )

        repr_str = repr(job)
        assert "ExtractionJob" in repr_str
        assert "statement.pdf" in repr_str
        assert "processing" in repr_str
        assert "balance_sheet" in repr_str


class TestExtractedStatement:
    """Tests for ExtractedStatement model."""

    def test_extracted_statement_creation(self):
        """Test creating an extracted statement."""
        statement = ExtractedStatement(
            extraction_job_id=1,
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="USD",
            total_line_items=0,
            has_errors=False,
        )

        assert statement.extraction_job_id == 1
        assert statement.statement_type == StatementType.INCOME_STATEMENT
        assert statement.company_name == "Test Corp"
        assert statement.period_start == "2024-01-01"
        assert statement.period_end == "2024-12-31"
        assert statement.fiscal_year == 2024
        assert statement.currency == "USD"
        assert statement.total_line_items == 0
        assert statement.has_errors is False

    def test_extracted_statement_with_errors(self):
        """Test extracted statement with validation errors."""
        statement = ExtractedStatement(
            extraction_job_id=1,
            statement_type=StatementType.BALANCE_SHEET,
            company_name="Test Inc",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="EUR",
            total_line_items=10,
            has_errors=True,
            validation_errors='{"errors": ["Missing totals"]}',
        )

        assert statement.has_errors is True
        assert statement.validation_errors is not None
        assert "Missing totals" in statement.validation_errors

    def test_extracted_statement_repr(self):
        """Test string representation of extracted statement."""
        statement = ExtractedStatement(
            extraction_job_id=1,
            statement_type=StatementType.CASH_FLOW,
            company_name="Cash Flow Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="USD",
            total_line_items=25,
        )

        repr_str = repr(statement)
        assert "ExtractedStatement" in repr_str
        assert "cash_flow" in repr_str
        assert "Cash Flow Corp" in repr_str
        assert "25" in repr_str


class TestExtractedLineItem:
    """Tests for ExtractedLineItem model."""

    def test_extracted_line_item_creation(self):
        """Test creating an extracted line item."""
        line_item = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Total Revenue",
            value=Decimal("1000000.00"),
            indent_level=0,
            order=1,
            is_header=False,
            is_total=False,
            is_calculated=False,
        )

        assert line_item.extracted_statement_id == 1
        assert line_item.line_item_name == "Total Revenue"
        assert line_item.value == Decimal("1000000.00")
        assert line_item.indent_level == 0
        assert line_item.order == 1
        assert line_item.is_header is False
        assert line_item.is_total is False
        assert line_item.is_calculated is False

    def test_extracted_line_item_with_hierarchy(self):
        """Test extracted line item with parent-child relationship."""
        parent = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Revenue",
            value=Decimal("1000000.00"),
            indent_level=0,
            order=1,
            section="Income",
            is_header=True,
        )

        child = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Product Revenue",
            value=Decimal("750000.00"),
            indent_level=1,
            order=2,
            parent_id=1,
            section="Income",
        )

        assert parent.is_header is True
        assert child.parent_id == 1
        assert child.indent_level == 1

    def test_extracted_line_item_calculated(self):
        """Test extracted line item with calculation."""
        line_item = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Net Income",
            value=Decimal("250000.00"),
            indent_level=0,
            order=10,
            is_total=True,
            is_calculated=True,
            formula="Revenue - Expenses",
        )

        assert line_item.is_total is True
        assert line_item.is_calculated is True
        assert line_item.formula == "Revenue - Expenses"

    def test_extracted_line_item_with_metadata(self):
        """Test extracted line item with additional metadata."""
        line_item = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Operating Expenses",
            category="Expense",
            value=Decimal("500000.00"),
            indent_level=0,
            order=5,
            notes="Includes salaries and overhead",
            raw_text="| Operating Expenses | $500,000 |",
            validation_warnings='{"warnings": ["Check against prior period"]}',
        )

        assert line_item.category == "Expense"
        assert line_item.notes == "Includes salaries and overhead"
        assert line_item.raw_text is not None
        assert line_item.validation_warnings is not None

    def test_extracted_line_item_repr(self):
        """Test string representation of extracted line item."""
        line_item = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Very Long Line Item Name That Should Be Truncated",
            value=Decimal("123456.78"),
            indent_level=2,
            order=1,
        )

        repr_str = repr(line_item)
        assert "ExtractedLineItem" in repr_str
        assert "123456.78" in repr_str
        assert "indent=2" in repr_str

    def test_extracted_line_item_high_precision(self):
        """Test extracted line item with high precision decimal."""
        line_item = ExtractedLineItem(
            extracted_statement_id=1,
            line_item_name="Precise Value",
            value=Decimal("123456.7890"),
            indent_level=0,
            order=1,
        )

        assert line_item.value == Decimal("123456.7890")
        # Verify precision is preserved
        assert str(line_item.value) == "123456.7890"
