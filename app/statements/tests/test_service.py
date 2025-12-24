"""Tests for statements service."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.schemas import WhisperResponse
from app.statements.models import StatementType
from app.statements.service import StatementProcessingError, StatementService


class TestStatementService:
    """Tests for StatementService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock(spec=AsyncSession)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create StatementService instance."""
        return StatementService(mock_db)

    @pytest.mark.asyncio
    async def test_create_statement(self, service, mock_db):
        """Test creating a statement."""
        await service.create_statement(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test Corp",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="USD",
        )

        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_create_statement_with_metadata(self, service, mock_db):
        """Test creating statement with extra metadata."""
        await service.create_statement(
            statement_type=StatementType.BALANCE_SHEET,
            company_name="Test Inc",
            period_start="2024-01-01",
            period_end="2024-12-31",
            fiscal_year=2024,
            currency="EUR",
            extra_metadata='{"source": "manual"}',
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_statement(self, service, mock_db):
        """Test getting a statement by ID."""
        # Mock query execution
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id=1)
        mock_db.execute.return_value = mock_result

        statement = await service.get_statement(1)

        assert statement is not None
        assert statement.id == 1
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_statement_not_found(self, service, mock_db):
        """Test getting non-existent statement."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        statement = await service.get_statement(999)

        assert statement is None

    @pytest.mark.asyncio
    async def test_get_statements_with_filters(self, service, mock_db):
        """Test getting statements with filters."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
        ]
        mock_db.execute.return_value = mock_result

        statements = await service.get_statements(
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test",
            fiscal_year=2024,
        )

        assert len(statements) == 2
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_statements_with_pagination(self, service, mock_db):
        """Test getting statements with pagination."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(id=1)]
        mock_db.execute.return_value = mock_result

        statements = await service.get_statements(limit=10, offset=20)

        assert len(statements) == 1
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_add_line_item(self, service, mock_db):
        """Test adding a line item to a statement."""
        # Mock statement exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id=1)
        mock_db.execute.return_value = mock_result

        await service.add_line_item(
            statement_id=1,
            line_item_name="Total Revenue",
            value=Decimal("1000000.00"),
            order=1,
            category="Revenue",
            indent_level=0,
        )

        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_add_line_item_with_parent(self, service, mock_db):
        """Test adding a line item with parent."""
        # Mock statement exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id=1)
        mock_db.execute.return_value = mock_result

        await service.add_line_item(
            statement_id=1,
            line_item_name="Product Revenue",
            value=Decimal("750000.00"),
            order=2,
            category="Revenue",
            indent_level=1,
            parent_id=1,
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_add_line_item_statement_not_found(self, service, mock_db):
        """Test adding line item to non-existent statement."""
        # Mock statement not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(StatementProcessingError, match="Statement 999 not found"):
            await service.add_line_item(
                statement_id=999,
                line_item_name="Test",
                value=Decimal("100.00"),
                order=1,
            )

    @pytest.mark.asyncio
    async def test_get_line_items(self, service, mock_db):
        """Test getting line items for a statement."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(id=1, order=1),
            MagicMock(id=2, order=2),
        ]
        mock_db.execute.return_value = mock_result

        line_items = await service.get_line_items(1)

        assert len(line_items) == 2
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_delete_statement(self, service, mock_db):
        """Test deleting a statement."""
        # Mock statement exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id=1)
        mock_db.execute.return_value = mock_result

        deleted = await service.delete_statement(1)

        assert deleted is True
        assert mock_db.delete.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_statement_not_found(self, service, mock_db):
        """Test deleting non-existent statement."""
        # Mock statement not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        deleted = await service.delete_statement(999)

        assert deleted is False
        assert not mock_db.delete.called

    @pytest.mark.asyncio
    @patch("app.statements.service.LLMWhispererClient")
    async def test_process_pdf_statement(self, mock_client_class, service, mock_db):
        """Test processing a PDF statement."""
        # Mock LLMWhisperer response
        mock_client = AsyncMock()
        mock_client.whisper.return_value = WhisperResponse(
            whisper_hash="test_hash_123",
            extracted_text="Sample extracted text from PDF",
            status_code=200,
            processing_time=1.5,
            page_count=3,
        )
        mock_client_class.return_value = mock_client
        service.llm_client = mock_client

        result = await service.process_pdf_statement(
            file_path="test.pdf",
            statement_type=StatementType.INCOME_STATEMENT,
            company_name="Test Corp",
            fiscal_year=2024,
        )

        assert result["extracted_text"] == "Sample extracted text from PDF"
        assert result["whisper_hash"] == "test_hash_123"
        assert result["page_count"] == 3
        assert result["statement_type"] == "income_statement"
        assert result["company_name"] == "Test Corp"
        assert result["fiscal_year"] == 2024

    @pytest.mark.asyncio
    @patch("app.statements.service.LLMWhispererClient")
    async def test_process_pdf_statement_error(self, mock_client_class, service, mock_db):
        """Test PDF processing error handling."""
        # Mock LLMWhisperer error
        mock_client = AsyncMock()
        mock_client.whisper.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        service.llm_client = mock_client

        with pytest.raises(StatementProcessingError, match="Failed to process PDF"):
            await service.process_pdf_statement(
                file_path="test.pdf",
                statement_type=StatementType.INCOME_STATEMENT,
                company_name="Test Corp",
                fiscal_year=2024,
            )

    def test_detect_statement_type_income(self, service, mock_db):
        """Test detecting income statement."""
        text = "ABC Company Income Statement for the year ended 2024 Revenue: $1M Net Income: $200K"
        statement_type, confidence = service.detect_statement_type(text)

        assert statement_type == StatementType.INCOME_STATEMENT
        assert confidence > 0.0

    def test_detect_statement_type_balance_sheet(self, service, mock_db):
        """Test detecting balance sheet."""
        text = "ABC Company Balance Sheet as of 2024-12-31 Assets: $5M Liabilities: $3M Equity: $2M"
        statement_type, confidence = service.detect_statement_type(text)

        assert statement_type == StatementType.BALANCE_SHEET
        assert confidence > 0.0

    def test_detect_statement_type_cash_flow(self, service, mock_db):
        """Test detecting cash flow statement."""
        text = """ABC Company Statement of Cash Flows Operating Activities: $500K
                  Investing Activities: ($200K) Financing Activities: $100K"""
        statement_type, confidence = service.detect_statement_type(text)

        assert statement_type == StatementType.CASH_FLOW
        assert confidence > 0.0

    def test_detect_statement_type_with_low_confidence(self, service, mock_db):
        """Test detection with ambiguous text."""
        text = "Some random financial document text without clear indicators"
        statement_type, confidence = service.detect_statement_type(text)

        # Should still return a type, but with low confidence
        assert isinstance(statement_type, StatementType)
        assert 0.0 <= confidence <= 1.0
