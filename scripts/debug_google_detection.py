"""Debug why Google PDFs aren't being detected."""

import sys
from pathlib import Path
import fitz

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extraction.page_detector import PageDetector
from dotenv import load_dotenv
load_dotenv()

# Test detection
detector = PageDetector()
pdf_path = Path("input/Google 2021-2023.pdf")

print(f"Testing detection on: {pdf_path}")
print("=" * 80)

# Run detection
results = detector.detect_financial_tables(pdf_path)

print(f"\nResults: {len(results)} statement types found")
for stmt_type, pages in results.items():
    print(f"  - {stmt_type.value}: Pages {pages}")

# Manual check on page 52 (balance sheet)
print("\n" + "=" * 80)
print("Manual validation of page 52 (should be balance sheet)")
print("=" * 80)

doc = fitz.open(str(pdf_path))
page = doc[51]  # Page 52 (0-indexed)

from app.extraction.page_detector import FinancialStatementType
stmt_type = FinancialStatementType.BALANCE_SHEET

# Test the actual validation method
is_valid, confidence = detector._is_actual_statement_page(page, stmt_type)

print(f"Is valid: {is_valid}")
print(f"Confidence: {confidence}")

# Check has_consolidated_header separately
has_header = detector._has_consolidated_header(page, stmt_type)
print(f"Has consolidated header: {has_header}")

# Check if it passes TOC/footnote filters
is_toc = detector._is_toc_entry(page)
is_footnote = detector._is_footnote_reference(page)
is_index = detector._is_index_entry(page)

print(f"\nFilters:")
print(f"  Is TOC: {is_toc}")
print(f"  Is footnote: {is_footnote}")
print(f"  Is index: {is_index}")

doc.close()
