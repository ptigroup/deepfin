"""Tests for PDF table detector."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.detection.detector import (
    PageDetectionResult,
    PDFTableDetector,
    TableBoundingBox,
    detect_tables_in_pdf,
)


class TestTableBoundingBox:
    """Tests for TableBoundingBox dataclass."""

    def test_bounding_box_creation(self):
        """Test creating a bounding box."""
        bb = TableBoundingBox(
            page=1,
            x0=10.0,
            y0=20.0,
            x1=100.0,
            y1=200.0,
            confidence=0.95,
        )
        assert bb.page == 1
        assert bb.x0 == 10.0
        assert bb.y0 == 20.0
        assert bb.x1 == 100.0
        assert bb.y1 == 200.0
        assert bb.confidence == 0.95

    def test_bounding_box_to_dict(self):
        """Test converting bounding box to dictionary."""
        bb = TableBoundingBox(
            page=1,
            x0=10.0,
            y0=20.0,
            x1=100.0,
            y1=200.0,
            confidence=0.95,
        )
        result = bb.to_dict()
        assert result == {
            "page": 1,
            "x0": 10.0,
            "y0": 20.0,
            "x1": 100.0,
            "y1": 200.0,
            "confidence": 0.95,
        }


class TestPageDetectionResult:
    """Tests for PageDetectionResult dataclass."""

    def test_page_result_creation(self):
        """Test creating a page detection result."""
        bb = TableBoundingBox(page=1, x0=10.0, y0=20.0, x1=100.0, y1=200.0)
        result = PageDetectionResult(
            page_number=1,
            table_count=2,
            confidence_score=0.85,
            bounding_boxes=[bb],
        )
        assert result.page_number == 1
        assert result.table_count == 2
        assert result.confidence_score == 0.85
        assert len(result.bounding_boxes) == 1

    def test_page_result_to_dict(self):
        """Test converting page result to dictionary."""
        bb = TableBoundingBox(page=1, x0=10.0, y0=20.0, x1=100.0, y1=200.0)
        result = PageDetectionResult(
            page_number=1,
            table_count=1,
            confidence_score=0.90,
            bounding_boxes=[bb],
        )
        result_dict = result.to_dict()
        assert result_dict["page_number"] == 1
        assert result_dict["table_count"] == 1
        assert result_dict["confidence_score"] == 0.90
        assert len(result_dict["bounding_boxes"]) == 1


class TestPDFTableDetector:
    """Tests for PDFTableDetector."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = PDFTableDetector()
        assert detector.min_confidence == 0.5

        detector = PDFTableDetector(min_confidence=0.7)
        assert detector.min_confidence == 0.7

    def test_detect_tables_file_not_found(self):
        """Test detection with non-existent file."""
        detector = PDFTableDetector()
        with pytest.raises(FileNotFoundError):
            detector.detect_tables("nonexistent.pdf")

    @patch("app.detection.detector.fitz.open")
    def test_detect_tables_invalid_pdf(self, mock_fitz_open):
        """Test detection with invalid PDF file."""
        mock_fitz_open.side_effect = Exception("Invalid PDF")
        detector = PDFTableDetector()

        # Create a temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to open PDF"):
                detector.detect_tables(temp_path)
        finally:
            Path(temp_path).unlink()

    @patch("app.detection.detector.fitz.open")
    def test_detect_tables_no_tables_found(self, mock_fitz_open):
        """Test detection when no tables are found."""
        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.find_tables.return_value = MagicMock(tables=[])
        mock_doc.__getitem__.return_value = mock_page

        mock_fitz_open.return_value = mock_doc

        detector = PDFTableDetector()

        # Create a temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            results = detector.detect_tables(temp_path)
            assert len(results) == 1
            assert results[0].page_number == 1
            assert results[0].table_count == 0
            assert results[0].confidence_score == 0.0
            assert len(results[0].bounding_boxes) == 0
        finally:
            Path(temp_path).unlink()
            mock_doc.close.assert_called_once()

    @patch("app.detection.detector.fitz.open")
    def test_detect_tables_with_tables_found(self, mock_fitz_open):
        """Test detection when tables are found."""
        # Mock PyMuPDF document and table
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Mock table with bbox and data
        mock_table = MagicMock()
        mock_table.bbox = (10.0, 20.0, 100.0, 200.0)
        mock_table.extract.return_value = [
            ["Header1", "Header2"],
            ["Value1", "Value2"],
            ["Value3", "Value4"],
        ]

        mock_tables = MagicMock()
        mock_tables.tables = [mock_table]

        mock_page = MagicMock()
        mock_page.find_tables.return_value = mock_tables
        mock_doc.__getitem__.return_value = mock_page

        mock_fitz_open.return_value = mock_doc

        detector = PDFTableDetector()

        # Create a temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            results = detector.detect_tables(temp_path)
            assert len(results) == 1
            assert results[0].page_number == 1
            assert results[0].table_count == 1
            assert results[0].confidence_score > 0.0
            assert len(results[0].bounding_boxes) == 1

            bb = results[0].bounding_boxes[0]
            assert bb.x0 == 10.0
            assert bb.y0 == 20.0
            assert bb.x1 == 100.0
            assert bb.y1 == 200.0
        finally:
            Path(temp_path).unlink()
            mock_doc.close.assert_called_once()

    def test_calculate_table_confidence(self):
        """Test table confidence calculation."""
        detector = PDFTableDetector()

        # Mock table with good data
        mock_table = MagicMock()
        mock_table.extract.return_value = [
            ["Header1", "Header2", "Header3"],
            ["Value1", "Value2", "Value3"],
            ["Value4", "Value5", "Value6"],
        ]

        confidence = detector._calculate_table_confidence(mock_table)
        assert 0.0 <= confidence <= 1.0
        # Should get bonuses for: multiple rows (0.2), consistent columns (0.2), header (0.1)
        assert confidence >= 0.8


@patch("app.detection.detector.fitz.open")
def test_detect_tables_in_pdf_convenience_function(mock_fitz_open):
    """Test the convenience function for detecting tables."""
    # Mock PyMuPDF document with 2 pages
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2

    # Page 1: 1 table
    mock_table1 = MagicMock()
    mock_table1.bbox = (10.0, 20.0, 100.0, 200.0)
    mock_table1.extract.return_value = [["H1", "H2"], ["V1", "V2"]]

    mock_tables1 = MagicMock()
    mock_tables1.tables = [mock_table1]

    mock_page1 = MagicMock()
    mock_page1.find_tables.return_value = mock_tables1

    # Page 2: No tables
    mock_page2 = MagicMock()
    mock_page2.find_tables.return_value = MagicMock(tables=[])

    mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
    mock_fitz_open.return_value = mock_doc

    # Create a temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        temp_path = f.name

    try:
        result = detect_tables_in_pdf(temp_path)

        assert result["total_pages"] == 2
        assert result["pages_with_tables"] == 1
        assert result["total_tables"] == 1
        assert len(result["pages"]) == 2

        # Page 1 should have 1 table
        assert result["pages"][0]["page_number"] == 1
        assert result["pages"][0]["table_count"] == 1

        # Page 2 should have 0 tables
        assert result["pages"][1]["page_number"] == 2
        assert result["pages"][1]["table_count"] == 0
    finally:
        Path(temp_path).unlink()
        mock_doc.close.assert_called_once()
