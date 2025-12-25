"""Tests for extraction service."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.extraction.models import ExtractionStatus, StatementType
from app.extraction.service import ExtractionService


class TestExtractionService:
    """Tests for ExtractionService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.mark.asyncio
    async def test_detect_statement_type_income(self):
        """Test detecting income statement type."""
        db = AsyncMock()
        service = ExtractionService(db)

        text = (
            "Income Statement for the year ending. Total Revenue: $1,000,000. Net Income: $250,000"
        )

        stmt_type, confidence = service._detect_statement_type(text)

        assert stmt_type == StatementType.INCOME_STATEMENT
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_detect_statement_type_balance_sheet(self):
        """Test detecting balance sheet type."""
        db = AsyncMock()
        service = ExtractionService(db)

        text = "Balance Sheet as of December 31. Total Assets: $5,000,000. Total Liabilities and Equity: $5,000,000"

        stmt_type, confidence = service._detect_statement_type(text)

        assert stmt_type == StatementType.BALANCE_SHEET
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_detect_statement_type_cash_flow(self):
        """Test detecting cash flow statement type."""
        db = AsyncMock()
        service = ExtractionService(db)

        text = "Cash Flow Statement. Operating Activities: $500,000. Investing Activities: ($200,000). Financing Activities: ($100,000)"

        stmt_type, confidence = service._detect_statement_type(text)

        assert stmt_type == StatementType.CASH_FLOW
        assert confidence > 0

    @pytest.mark.asyncio
    async def test_detect_statement_type_unknown(self):
        """Test unknown statement type."""
        db = AsyncMock()
        service = ExtractionService(db)

        text = "This document does not contain financial keywords"

        stmt_type, confidence = service._detect_statement_type(text)

        assert stmt_type == StatementType.UNKNOWN
        assert confidence == 0.0

    @pytest.mark.asyncio
    async def test_extract_company_name(self):
        """Test extracting company name from text."""
        db = AsyncMock()
        service = ExtractionService(db)

        text = """Acme Corporation
Income Statement
For the Year Ended December 31, 2024"""

        company_name = service._extract_company_name(text)

        assert "Acme" in company_name or company_name != "Unknown"

    @pytest.mark.asyncio
    async def test_extract_fiscal_year(self):
        """Test extracting fiscal year from period text."""
        db = AsyncMock()
        service = ExtractionService(db)

        # Various formats
        assert service._extract_fiscal_year("2024") == 2024
        assert service._extract_fiscal_year("FY 2023") == 2023
        assert service._extract_fiscal_year("Year ending 2022") == 2022
        assert service._extract_fiscal_year("no year") == 0

    @pytest.mark.asyncio
    async def test_determine_periods(self):
        """Test determining period start and end dates."""
        db = AsyncMock()
        service = ExtractionService(db)

        # With valid year
        start, end = service._determine_periods(["2024", "2023"])
        assert start == "2024-01-01"
        assert end == "2024-12-31"

        # Without year
        start, end = service._determine_periods([])
        assert start == "1900-01-01"
        assert end == "1900-12-31"

    @pytest.mark.asyncio
    async def test_calculate_file_hash(self):
        """Test file hash calculation."""
        db = AsyncMock()
        service = ExtractionService(db)

        # Create temp file
        temp_file = Path("/tmp/test_file.txt")
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text("test content")

        hash1 = service._calculate_file_hash(temp_file)
        hash2 = service._calculate_file_hash(temp_file)

        # Same file should have same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

        # Cleanup
        temp_file.unlink()

    @pytest.mark.asyncio
    async def test_get_jobs_with_status_filter(self, mock_db):
        """Test getting jobs with status filter."""
        service = ExtractionService(mock_db)

        # Mock execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        jobs = await service.get_jobs(status=ExtractionStatus.COMPLETED)

        assert isinstance(jobs, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_jobs_with_pagination(self, mock_db):
        """Test getting jobs with pagination."""
        service = ExtractionService(mock_db)

        # Mock execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        jobs = await service.get_jobs(skip=10, limit=50)

        assert isinstance(jobs, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_job_by_id(self, mock_db):
        """Test getting job by ID."""
        service = ExtractionService(mock_db)

        # Mock execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        job = await service.get_job(123)

        assert job is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_job_by_hash_exists(self, mock_db):
        """Test getting existing job by file hash."""
        service = ExtractionService(mock_db)

        # Mock existing job
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.status = ExtractionStatus.COMPLETED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        job = await service._get_job_by_hash("abc123")

        assert job is not None
        assert job.id == 1

    @pytest.mark.asyncio
    async def test_get_job_by_hash_not_exists(self, mock_db):
        """Test getting non-existent job by hash."""
        service = ExtractionService(mock_db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        job = await service._get_job_by_hash("nonexistent")

        assert job is None
