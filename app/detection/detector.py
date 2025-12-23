"""PDF table detection using PyMuPDF."""

import logging
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class TableBoundingBox:
    """Represents a table's bounding box coordinates."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "page": self.page,
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "confidence": self.confidence,
        }


@dataclass
class PageDetectionResult:
    """Detection result for a single page."""

    page_number: int
    table_count: int
    confidence_score: float
    bounding_boxes: list[TableBoundingBox]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "page_number": self.page_number,
            "table_count": self.table_count,
            "confidence_score": self.confidence_score,
            "bounding_boxes": [bb.to_dict() for bb in self.bounding_boxes],
        }


class PDFTableDetector:
    """Detects tables in PDF documents using PyMuPDF."""

    def __init__(self, min_confidence: float = 0.5):
        """
        Initialize PDF table detector.

        Args:
            min_confidence: Minimum confidence threshold for table detection
        """
        self.min_confidence = min_confidence

    def detect_tables(self, pdf_path: str | Path) -> list[PageDetectionResult]:
        """
        Detect tables in a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of detection results per page

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}") from e

        try:
            results = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_result = self._detect_tables_in_page(page, page_num + 1)
                results.append(page_result)

            return results
        finally:
            doc.close()

    def _detect_tables_in_page(self, page: fitz.Page, page_number: int) -> PageDetectionResult:
        """
        Detect tables in a single page.

        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number

        Returns:
            Detection result for the page
        """
        try:
            # PyMuPDF's find_tables() returns table objects
            tables = page.find_tables()

            if not tables or len(tables.tables) == 0:
                logger.debug(f"No tables found on page {page_number}")
                return PageDetectionResult(
                    page_number=page_number,
                    table_count=0,
                    confidence_score=0.0,
                    bounding_boxes=[],
                )

            # Extract bounding boxes for each detected table
            bounding_boxes = []
            confidences = []

            for table in tables.tables:
                # Get table bounding box (bbox)
                bbox = table.bbox
                if bbox:
                    # PyMuPDF bbox format: (x0, y0, x1, y1)
                    # Calculate confidence based on table structure
                    confidence = self._calculate_table_confidence(table)
                    confidences.append(confidence)

                    if confidence >= self.min_confidence:
                        bounding_boxes.append(
                            TableBoundingBox(
                                page=page_number,
                                x0=bbox[0],
                                y0=bbox[1],
                                x1=bbox[2],
                                y1=bbox[3],
                                confidence=confidence,
                            )
                        )

            # Calculate overall page confidence (average of all table confidences)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(
                f"Page {page_number}: Found {len(bounding_boxes)} tables "
                f"(confidence: {avg_confidence:.2f})"
            )

            return PageDetectionResult(
                page_number=page_number,
                table_count=len(bounding_boxes),
                confidence_score=round(avg_confidence, 4),
                bounding_boxes=bounding_boxes,
            )

        except Exception as e:
            logger.error(f"Error detecting tables on page {page_number}: {e}")
            return PageDetectionResult(
                page_number=page_number,
                table_count=0,
                confidence_score=0.0,
                bounding_boxes=[],
            )

    def _calculate_table_confidence(self, table) -> float:
        """
        Calculate confidence score for a detected table.

        Args:
            table: PyMuPDF table object

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Base confidence
            confidence = 0.5

            # Extract table data
            rows = table.extract()

            # Bonus for having multiple rows
            if len(rows) >= 3:
                confidence += 0.2

            # Bonus for having consistent columns
            if rows:
                col_counts = [len(row) for row in rows if row]
                if col_counts and len(set(col_counts)) == 1:  # All rows have same columns
                    confidence += 0.2

            # Bonus for having header row (first row often has headers)
            if len(rows) >= 2:
                confidence += 0.1

            return min(confidence, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating table confidence: {e}")
            return 0.5  # Default confidence


def detect_tables_in_pdf(pdf_path: str | Path) -> dict:
    """
    Convenience function to detect tables in a PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with detection results

    Example:
        >>> result = detect_tables_in_pdf("document.pdf")
        >>> print(f"Found {result['total_tables']} tables across {result['total_pages']} pages")
    """
    detector = PDFTableDetector()
    results = detector.detect_tables(pdf_path)

    # Aggregate results
    total_tables = sum(r.table_count for r in results)
    total_pages = len(results)
    pages_with_tables = sum(1 for r in results if r.table_count > 0)

    return {
        "total_pages": total_pages,
        "pages_with_tables": pages_with_tables,
        "total_tables": total_tables,
        "pages": [r.to_dict() for r in results],
    }
