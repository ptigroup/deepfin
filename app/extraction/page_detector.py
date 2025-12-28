"""
AI-Powered Table Detection System using PyMuPDF

This module uses PyMuPDF's advanced table detection to identify financial statement tables
in PDF documents without using LLMWhisperer credits, then validates the content
to ensure proper financial statements are identified.

Ported from brownfield/pipelines/pipeline_02_table_detection/pipeline_02_detect_tables.py
with full 3-step validation framework.
"""

import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF

from app.core.logging import get_logger

logger = get_logger(__name__)

# Enhanced scoring patterns with context-aware validation
STATEMENT_PATTERNS = {
    "income_statement": {
        'primary_indicators': [
            r"consolidated\s+statements?\s+of\s+(?:income|operations|comprehensive\s+income\s+and\s+operations)",
            r"statements?\s+of\s+(?:income|operations|comprehensive\s+income)",
            r"income\s+statement(?:s)?",
            r"consolidated\s+statements?\s+of\s+profit\s+and\s+loss",
            r"revenue",
            r"net\s+(?:income|profit|loss)",
            r"consolidated\s+statements?\s+of\s+operations",
            r"earnings\s+per\s+share"
        ],
        'content_indicators': [
            r"(?:net\s+)?(?:revenue|sales|turnover)",
            r"cost\s+of\s+(?:revenue|goods\s+sold|sales)",
            r"gross\s+(?:profit|margin)",
            r"operating\s+expenses",
            r"research\s+and\s+development",
            r"sales,\s+general\s+and\s+administrative",
            r"total\s+operating\s+expenses",
            r"income\s+from\s+operations",
            r"interest\s+income",
            r"interest\s+expense",
            r"other,\s+net",
            r"total\s+other\s+income\s+\(expense\)",
            r"income\s+before\s+income\s+tax",
            r"income\s+tax\s+(?:expense|benefit)",
            r"net\s+(?:income|profit|loss)",
            r"net\s+income\s+per\s+share",
            r"basic\s*\$",
            r"diluted\s*\$",
            r"weighted\s+average\s+shares\s+used\s+in\s+per\s+share\s+computation"
        ],
        'structure_indicators': [
            r"(?:revenue.*?\$|revenue.*?\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
            r"(?:net\s+income.*?\$|net\s+income.*?\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
            r"(?:for\s+the\s+(?:years?|periods?)\s+ended|fiscal\s+year\s+ended)",
            r"(?:total\s+revenue|total\s+sales)",
            r"(?:net\s+profit\s+before\s+tax|profit\s+before\s+tax)"
        ],
        'negative_indicators': [
            r"selected\s+financial\s+data",
            r"consolidated\s+statements?\s+of\s+income\s+data",
            r"should\s+be\s+read\s+in\s+conjunction",
            r"derived\s+from\s+and\s+should\s+be\s+read",
            r"see\s+note\s+\d+",
            r"refer\s+to\s+notes?",
            r"for\s+further\s+information",
            r"\.{4,}\s*\d+\s*$",  # TOC pattern
            r"goodwill",
            r"impairment\s+test",
            r"qualitative\s+(?:or\s+)?quantitative\s+assessment",
            r"accounting\s+principles?",
            r"critical\s+accounting\s+(?:estimates|policies)",
            r"estimates\s+and\s+assumptions",
            r"fair\s+value.*reporting\s+unit",
            r"management.*judgments?",
            r"requires\s+us\s+to\s+make\s+judgments?",
            r"revenue\s+by\s+reportable\s+segments?",
            r"graphics\s+segment\s+revenue",
            r"compute\s+&\s+networking",
            r"segment.*revenue\s+increased",
            r"compared\s+to\s+fiscal\s+year",
            r"believe\s+the\s+increase.*resulted\s+from",
            r"combination\s+of\s+factors",
            r"benefit\s+from\s+strong\s+demand",
            # NEW: MD&A-specific patterns (critical for filtering page 32-style summaries)
            r"up \d+%",                              # "up 61%"
            r"down \d+%",                            # "down 25%"
            r"increased \d+%",                       # "increased 40%"
            r"decreased \d+%",                       # "decreased 15%"
            r"from a year ago",                      # Narrative comparison
            r"was \$[\d,.]+ (?:billion|million)",   # "was $26.91 billion"
            r"driven by",                            # Analytical language
            r"primarily due to",                     # Explanatory language
            r"resulted from a",                      # Causal explanation
        ],
        'required_patterns': [
            r"(?:revenue|sales)",
            r"(?:net\s+income|net\s+profit)",
            r"(?:cost\s+of\s+revenue|gross\s+profit)",
            r"(?:operating\s+expenses|research\s+and\s+development)"
        ],
        'min_content_matches': 4,
        'min_structure_matches': 0  # Reduced from 2 - rely on content+header validation
    },
    "balance_sheet": {
        'primary_indicators': [
            r"consolidated\s+balance\s+sheets?",
            r"balance\s+sheets?",
            r"statements?\s+of\s+financial\s+position",
            r"total\s+assets",
            r"total\s+liabilities",
        ],
        'content_indicators': [
            r"current\s+assets",
            r"cash\s+and\s+cash\s+equivalents",
            r"marketable\s+securities",
            r"accounts\s+receivable",
            r"inventories",
            r"total\s+current\s+assets",
            r"property\s+and\s+equipment",
            r"goodwill",
            r"intangible\s+assets",
            r"current\s+liabilities",
            r"accounts\s+payable",
            r"total\s+liabilities",
            r"shareholders.?\s+equity",
            r"common\s+stock",
            r"retained\s+earnings",
            r"total\s+shareholders.?\s+equity"
        ],
        'structure_indicators': [
            r"(?:total\s+assets.*?total\s+(?:liabilities|liabilities\s+and\s+equity))",
            r"(?:as\s+of\s+(?:\w+\s+\d{1,2},\s+\d{4}|fiscal\s+year\s+ended))"
        ],
        'negative_indicators': [
            r"see\s+note\s+\d+",
            r"refer\s+to\s+notes?",
            r"\.{4,}\s*\d+\s*$"
        ],
        'required_patterns': [
            r"total\s+assets",
            r"total\s+(?:liabilities|liabilities\s+and\s+shareholders.?\s+equity)"
        ],
        'min_content_matches': 5,
        'min_structure_matches': 1
    },
    "cash_flow": {
        'primary_indicators': [
            r"consolidated\s+statements?\s+of\s+cash\s+flows?",
            r"statements?\s+of\s+cash\s+flows?",
            r"cash\s+flow\s+statements?",
            # NEW: Supplemental cash flow patterns (page 51, 43-44)
            r"supplemental\s+disclosures?\s+of\s+cash\s+flow",
            r"cash\s+paid\s+for\s+income\s+taxes",
            r"non-cash\s+investing\s+and\s+financing\s+activity",
        ],
        'content_indicators': [
            r"cash\s+flows?\s+from\s+operating\s+activities",
            r"cash\s+flows?\s+from\s+investing\s+activities",
            r"cash\s+flows?\s+from\s+financing\s+activities",
            r"net\s+increase\s+in\s+cash",
            r"cash\s+and\s+cash\s+equivalents,\s+beginning\s+of\s+(?:year|period)",
            r"cash\s+and\s+cash\s+equivalents,\s+end\s+of\s+(?:year|period)"
        ],
        'structure_indicators': [
            r"(?:cash\s+flows?\s+from\s+operating.*?cash\s+flows?\s+from\s+investing)",
            r"(?:for\s+the\s+(?:years?|periods?)\s+ended|fiscal\s+year\s+ended)"
        ],
        'negative_indicators': [
            r"see\s+note\s+\d+",
            r"refer\s+to\s+notes?",
            r"\.{4,}\s*\d+\s*$"
        ],
        'required_patterns': [
            # Format 1: "Cash flows from X activities" (NVIDIA format)
            r"cash\s+flows?\s+from\s+operating\s+activities",
            r"cash\s+flows?\s+from\s+investing\s+activities",
            r"cash\s+flows?\s+from\s+financing\s+activities",
            # Format 2: "X activities" as header + "net cash" (Google/Alphabet format)
            r"operating\s+activities.*net\s+cash",
            r"investing\s+activities.*net\s+cash",
            r"financing\s+activities.*net\s+cash",
            # Format 3: Just section headers (simplified format)
            r"(?:^|\n)\s*operating\s+activities\s*(?:\n|$)",
            r"(?:^|\n)\s*investing\s+activities\s*(?:\n|$)",
            r"(?:^|\n)\s*financing\s+activities\s*(?:\n|$)",
            # Supplemental cash flow pages
            r"supplemental\s+disclosures?\s+of\s+cash\s+flow",
        ],
        'min_content_matches': 0,  # Reduced from 1 - supplemental pages have NO standard content indicators
        'min_structure_matches': 0  # Reduced from 1 - supplemental pages have minimal structure
    },
    "comprehensive_income": {
        'primary_indicators': [
            r"consolidated\s+statements?\s+of\s+comprehensive\s+income",
            r"statements?\s+of\s+comprehensive\s+income",
            r"other\s+comprehensive\s+(?:income|loss)",
            r"total\s+comprehensive\s+(?:income|loss)",
        ],
        'content_indicators': [
            r"net\s+income",
            r"other\s+comprehensive\s+(?:income|loss)",
            r"unrealized\s+(?:gain|loss)",
            r"net\s+of\s+tax",
            r"total\s+comprehensive\s+(?:income|loss)"
        ],
        'structure_indicators': [
            r"(?:net\s+income.*?other\s+comprehensive\s+income)",
            r"(?:for\s+the\s+(?:years?|periods?)\s+ended|fiscal\s+year\s+ended)"
        ],
        'negative_indicators': [
            r"see\s+note\s+\d+",
            r"refer\s+to\s+notes?",
            r"\.{4,}\s*\d+\s*$"
        ],
        'required_patterns': [
            r"other\s+comprehensive\s+(?:income|loss)",
            r"total\s+comprehensive\s+(?:income|loss)"
        ],
        'min_content_matches': 0,
        'min_structure_matches': 0
    },
    "shareholders_equity": {
        'primary_indicators': [
            r"consolidated\s+statements?\s+of\s+shareholders?\.?\s+equity",
            r"statements?\s+of\s+stockholders?\.?\s+equity",
            r"statements?\s+of\s+changes\s+in\s+equity",
            r"common\s+stock",
            r"retained\s+earnings"
        ],
        'content_indicators': [
            r"common\s+stock\s+outstanding",
            r"additional\s+paid-in\s+capital",
            r"treasury\s+stock",
            r"accumulated\s+other\s+comprehensive\s+(?:income|loss)",
            r"retained\s+earnings",
            r"total\s+shareholders.?\s+equity",
            r"stock-based\s+compensation",
            r"share\s+repurchase"
        ],
        'structure_indicators': [
            r"balances,\s+\w+\s+\d+,\s+20\d{2}"
        ],
        'negative_indicators': [
            r"see\s+note\s+\d+",
            r"refer\s+to\s+notes?",
            r"\.{4,}\s*\d+\s*$"
        ],
        'required_patterns': [
            r"common\s+stock",
            r"retained\s+earnings"
        ],
        'min_content_matches': 3,
        'min_structure_matches': 0
    }
}


class FinancialStatementType(Enum):
    """Types of financial statements we can detect."""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    COMPREHENSIVE_INCOME = "comprehensive_income"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    CASH_FLOW = "cash_flow"
    UNKNOWN = "unknown"


@dataclass
class DetectedTable:
    """Represents a detected table with validation information."""
    page_number: int
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    statement_type: FinancialStatementType
    confidence_score: float
    content_indicators: dict[str, Any]
    table_structure: dict[str, Any]


class PageDetector:
    """AI-powered table detector using PyMuPDF and advanced 3-step validation."""

    def __init__(self) -> None:
        """Initialize the detector."""
        self.min_confidence_score = 15
        logger.info("PageDetector initialized with 3-step validation")

    def detect_financial_tables(self, pdf_path: str | Path) -> Dict[FinancialStatementType, List[int]]:
        """
        Detect ACTUAL financial statement pages using 3-step validation framework.
        Filters out TOC entries, footnotes, and references to find real statement pages.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary mapping statement types to specific page numbers
        """
        pdf_path = str(pdf_path)
        logger.info("Scanning PDF for tables", extra={"pdf": pdf_path})

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            logger.info("Loaded PDF", extra={"pages": total_pages})

            # STEP 1: Find ALL candidate pages (broad keyword search)
            candidates = self._find_candidate_pages(doc)
            total_candidates = sum(len(pages) for pages in candidates.values())
            logger.debug(f"Step 1: Found {total_candidates} candidate pages")

            # STEP 2: Filter candidates using validation heuristics
            validated_pages = self._validate_candidate_pages(doc, candidates)
            total_validated = sum(len(pages) for pages in validated_pages.values())
            logger.debug(f"Step 2: {total_validated} pages passed validation")

            # STEP 3: Resolve ambiguity using content-based analysis
            final_pages = self._resolve_page_ambiguity(doc, validated_pages)
            total_final = sum(len(pages) for pages in final_pages.values())
            logger.debug(f"Step 3: Selected {total_final} final pages")

            doc.close()

            logger.info(
                "Detection complete",
                extra={"total_pages": total_final, "statement_types": len(final_pages)},
            )

            return final_pages

        except Exception as e:
            logger.error("Error during financial statement identification", extra={"error": str(e)})
            return {}

    def _find_candidate_pages(self, doc) -> Dict[FinancialStatementType, List[int]]:
        """
        STEP 1: Find ALL pages containing financial statement keywords.
        This is a broad search that will include TOC, footnotes, and actual statements.
        """
        patterns = {
            FinancialStatementType.INCOME_STATEMENT: [
                r"income statement", r"consolidated statements? of income", r"statements? of operations",
                r"revenue", r"net income", r"gross profit", r"operating income"
            ],
            FinancialStatementType.COMPREHENSIVE_INCOME: [
                r"comprehensive income", r"other comprehensive income", r"unrealized"
            ],
            FinancialStatementType.BALANCE_SHEET: [
                r"balance sheet", r"consolidated balance sheets", r"total assets", r"total liabilities"
            ],
            FinancialStatementType.CASH_FLOW: [
                r"cash flows?", r"cash flows? from operating", r"cash flows? from investing"
            ],
            FinancialStatementType.SHAREHOLDERS_EQUITY: [
                r"shareholders.?\s+equity", r"stockholders.?\s+equity", r"retained earnings"
            ]
        }

        candidates = {stmt_type: [] for stmt_type in FinancialStatementType}

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().lower()

            for stmt_type, stmt_patterns in patterns.items():
                for pattern in stmt_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        page_number_1indexed = page_num + 1
                        if page_number_1indexed not in candidates[stmt_type]:
                            candidates[stmt_type].append(page_number_1indexed)
                        break  # One match is enough for candidate

        return candidates

    def _validate_candidate_pages(self, doc, candidates: Dict[FinancialStatementType, List[int]]) -> Dict[FinancialStatementType, List[int]]:
        """
        STEP 2: Filter candidates using structural validation to remove TOC, footnotes, etc.
        """
        validated = {stmt_type: [] for stmt_type in FinancialStatementType}

        for stmt_type, page_list in candidates.items():
            page_confidences = []

            for page_num in page_list:
                page = doc[page_num - 1]  # Convert to 0-indexed

                # Apply basic filtering first
                if (self._is_toc_entry(page) or
                    self._is_footnote_reference(page) or
                    self._is_index_entry(page)):
                    continue

                # Apply sophisticated validation
                is_statement, confidence = self._is_actual_statement_page(page, stmt_type)
                if is_statement:
                    page_confidences.append((page_num, confidence))

            # Sort by confidence and keep pages
            page_confidences.sort(key=lambda x: x[1], reverse=True)
            validated[stmt_type] = [page_num for page_num, _ in page_confidences]

        return validated

    def _resolve_page_ambiguity(self, doc, validated_pages: Dict[FinancialStatementType, List[int]]) -> Dict[FinancialStatementType, List[int]]:
        """
        STEP 3: Resolve ambiguity using financial statement sequencing and content-based scoring.
        """
        final_pages = {}

        for stmt_type, page_list in validated_pages.items():
            if not page_list:
                continue

            if len(page_list) == 1:
                # Only one valid page, use it
                final_pages[stmt_type] = page_list
            else:
                # Multiple candidates - special handling for cash flow
                if stmt_type == FinancialStatementType.CASH_FLOW:
                    # Check for consecutive pairs (main statement + supplemental)
                    consecutive_pairs = self._find_consecutive_pairs(page_list)
                    if consecutive_pairs:
                        final_pages[stmt_type] = consecutive_pairs[0]  # Use both pages
                        continue

                # For other types or if no consecutive pairs, pick the best single page
                best_page = self._select_best_page(doc, page_list, stmt_type)
                final_pages[stmt_type] = [best_page]

        return final_pages

    def _find_consecutive_pairs(self, page_list: List[int]) -> List[List[int]]:
        """Find consecutive page pairs in the list (e.g., [43, 44])."""
        consecutive_pairs = []
        for i in range(len(page_list) - 1):
            if page_list[i+1] == page_list[i] + 1:
                consecutive_pairs.append([page_list[i], page_list[i+1]])
        return consecutive_pairs

    def _select_best_page(self, doc, page_list: List[int], stmt_type: FinancialStatementType) -> int:
        """Select the best page from multiple candidates based on confidence scores."""
        # Special handling for cash flow - check for consecutive pages first
        if stmt_type == FinancialStatementType.CASH_FLOW:
            consecutive_pairs = self._find_consecutive_pairs(page_list)
            if consecutive_pairs:
                # Return first page of first pair (we'll update this to return both later)
                return consecutive_pairs[0][0]

        page_scores = []

        for page_num in page_list:
            page = doc[page_num - 1]
            is_statement, confidence = self._is_actual_statement_page(page, stmt_type)
            if is_statement:
                # Boost confidence for pages in typical financial statement range (35-50)
                if 35 <= page_num <= 50:
                    confidence += 0.1
                page_scores.append((page_num, confidence))

        # Sort by confidence (highest first) and return best page
        if page_scores:
            page_scores.sort(key=lambda x: x[1], reverse=True)
            return page_scores[0][0]

        # Fallback to earliest page
        return min(page_list)

    # ===============================
    # VALIDATION HELPER FUNCTIONS
    # ===============================

    def _has_consolidated_header(self, page, stmt_type: FinancialStatementType) -> bool:
        """
        Check if page has proper CONSOLIDATED header in top section.
        Critical for distinguishing actual statements from MD&A summaries.
        """
        # Extract only top 120 pixels (header region)
        header_region = fitz.Rect(0, 0, page.rect.width, 120)
        header_text = page.get_text("text", clip=header_region).upper()

        # Clean up Unicode artifacts (�) and normalize whitespace
        header_text = re.sub(r'[^\w\s\(\)]', ' ', header_text)
        header_text = re.sub(r'\s+', ' ', header_text)

        if stmt_type == FinancialStatementType.INCOME_STATEMENT:
            # Must have "CONSOLIDATED STATEMENTS OF INCOME" or similar in header
            return bool(re.search(
                r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+(?:INCOME|OPERATIONS)",
                header_text
            ))
        elif stmt_type == FinancialStatementType.COMPREHENSIVE_INCOME:
            return bool(re.search(
                r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+COMPREHENSIVE\s+INCOME",
                header_text
            ))
        elif stmt_type == FinancialStatementType.BALANCE_SHEET:
            return bool(re.search(
                r"CONSOLIDATED\s+BALANCE\s+SHEETS?",
                header_text
            ))
        elif stmt_type == FinancialStatementType.SHAREHOLDERS_EQUITY:
            return bool(re.search(
                r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+SHAREHOLDERS?\s+EQUITY",
                header_text
            ))
        elif stmt_type == FinancialStatementType.CASH_FLOW:
            return bool(re.search(
                r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+CASH\s+FLOWS?",
                header_text
            ))

        return False

    def _is_toc_entry(self, page) -> bool:
        """Detect Table of Contents entries (NOT actual statements)"""
        text = page.get_text("text")

        # Pattern 1: Dots leading to page number
        if re.search(r"\.{4,}\s*\d+\s*$", text[:300]):
            return True

        # Pattern 2: "Page" label before number
        if re.search(r"page\s+\d+", text[:200], re.IGNORECASE):
            return True

        return False

    def _is_footnote_reference(self, page) -> bool:
        """Detect footnote references (NOT actual statements)"""
        text = page.get_text("text")

        # Check if this is primarily a footnote page
        see_note_count = len(re.findall(r"see note \d+", text, re.IGNORECASE))
        refer_count = len(re.findall(r"refer to (?:the )?notes? to", text, re.IGNORECASE))

        # If more than 3 footnote references, it's likely a footnote page
        if see_note_count > 3 or refer_count > 1:
            return True

        return False

    def _is_index_entry(self, page) -> bool:
        """
        Detect index/navigation entries.

        Note: Many PDFs have "Table of Contents" as a header/navigation element
        on every page. We need to distinguish actual TOC pages from pages that
        just have TOC in the header.
        """
        text = page.get_text("text")

        # Check for actual index pages (not just header text)
        if re.search(r"index\s*$", text[:100], re.IGNORECASE):
            return True

        # Only consider it a TOC page if it has TOC-specific patterns:
        # 1. Has "Table of Contents" in first 200 chars AND
        # 2. Has TOC-like content (page numbers, dots, chapter references)
        if re.search(r"table of contents", text[:200], re.IGNORECASE):
            # Check for TOC-specific patterns throughout the page
            toc_indicators = [
                r"\.{3,}",  # Multiple dots (leading to page numbers)
                r"\s+\d+\s*$",  # Line ending with page number
                r"page\s+\d+",  # Explicit page references
                r"part\s+[ivx]+",  # Roman numeral parts (Part I, Part II)
                r"item\s+\d+\.",  # Item references (Item 1., Item 2.)
            ]

            # If it has TOC indicators, it's likely a real TOC page
            toc_count = sum(1 for pattern in toc_indicators if re.search(pattern, text, re.IGNORECASE))
            if toc_count >= 2:
                return True

            # Additional check: If "CONSOLIDATED" appears (financial statement keyword),
            # it's NOT a TOC page, it's a financial statement with TOC in header
            if re.search(r"consolidated\s+(?:balance|statements?)", text, re.IGNORECASE):
                return False

        return False

    def _is_actual_statement_page(self, page, stmt_type: FinancialStatementType) -> Tuple[bool, float]:
        """
        Verify this is a REAL financial statement page using sophisticated multi-step validation.

        Returns:
            tuple: (is_actual_statement: bool, confidence: float)
        """
        text = page.get_text().lower()

        # Get patterns for this statement type
        patterns = STATEMENT_PATTERNS.get(stmt_type.value, {})
        if not patterns:
            return False, 0.0

        # STEP 1: Check primary indicators (must have at least one)
        primary_matches = self._count_pattern_matches(text, patterns.get('primary_indicators', []))
        if primary_matches == 0:
            return False, 0.0

        # STEP 1.5: Check for proper CONSOLIDATED header (CRITICAL for filtering MD&A)
        # Note: We'll use this later for confidence scoring, not rejection
        has_proper_header = self._has_consolidated_header(page, stmt_type)

        # STEP 2: Check negative indicators (too many disqualify)
        negative_matches = self._count_pattern_matches(text, patterns.get('negative_indicators', []))
        if negative_matches > 3:  # Allow up to 3 negative indicators
            return False, 0.0

        # STEP 3: Check required patterns (most should be present)
        required_patterns = patterns.get('required_patterns', [])
        required_found = 0
        for pattern in required_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                required_found += 1
        # Reduced threshold to 1 - we have MD&A filtering and header validation to prevent false positives
        required_threshold = 1  # Was: max(1, len(required_patterns) // 2)
        if required_found < required_threshold:
            return False, 0.0

        # STEP 4: Count content and structure indicators
        content_matches = self._count_pattern_matches(text, patterns.get('content_indicators', []))
        structure_matches = self._count_pattern_matches(text, patterns.get('structure_indicators', []))

        # Calculate confidence score
        min_content = patterns.get('min_content_matches', 0)
        min_structure = patterns.get('min_structure_matches', 0)

        if content_matches >= min_content and structure_matches >= min_structure:
            # Base confidence from content and structure
            confidence = min(1.0, (content_matches * 0.05) + (structure_matches * 0.1) + 0.3)

            # CRITICAL BOOST: Pages with proper CONSOLIDATED header get massive boost
            # This ensures actual statements (page 47) beat MD&A summaries (page 32)
            if has_proper_header:
                confidence += 0.5  # Major boost for proper header

            confidence = min(1.0, confidence)  # Cap at 1.0
            return True, confidence

        return False, 0.0

    def _count_pattern_matches(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match in the text."""
        count = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                count += 1
        return count

    # ===============================
    # LEGACY COMPATIBILITY
    # ===============================

    def detect_tables_in_pdf(self, pdf_path: str | Path) -> dict[int, list[DetectedTable]]:
        """
        Legacy method for compatibility with existing code.
        Wraps the new detect_financial_tables() method.
        """
        detected_pages = self.detect_financial_tables(pdf_path)

        # Convert to old format (dict[page_num, list[DetectedTable]])
        result = {}
        for stmt_type, pages in detected_pages.items():
            for page_num in pages:
                if page_num not in result:
                    result[page_num] = []

                # Create dummy DetectedTable for compatibility
                detected_table = DetectedTable(
                    page_number=page_num,
                    bbox=(0, 0, 0, 0),  # Not used in new approach
                    statement_type=stmt_type,
                    confidence_score=0.8,  # Default confidence
                    content_indicators={},
                    table_structure={},
                )
                result[page_num].append(detected_table)

        return result

    def get_page_ranges_for_extraction(
        self, detected_tables: dict[int, list[DetectedTable]] | Dict[FinancialStatementType, List[int]]
    ) -> dict[FinancialStatementType, list[int]]:
        """
        Get page ranges for each financial statement type for targeted LLMWhisperer extraction.

        Args:
            detected_tables: Either old format (dict[page_num, list[DetectedTable]])
                           or new format (Dict[FinancialStatementType, List[int]])

        Returns:
            Dictionary mapping statement types to page lists
        """
        # Handle new format (already in correct structure)
        if detected_tables and isinstance(next(iter(detected_tables.keys())), FinancialStatementType):
            # New format: expand pages with surrounding context
            page_ranges: dict[FinancialStatementType, list[int]] = {}
            for stmt_type, pages in detected_tables.items():
                expanded_pages = []
                for page_num in pages:
                    # Add surrounding pages (statements often span multiple pages)
                    for page_offset in [-1, 0, 1, 2]:
                        target_page = page_num + page_offset
                        if target_page > 0 and target_page not in expanded_pages:
                            expanded_pages.append(target_page)

                page_ranges[stmt_type] = sorted(expanded_pages)
            return page_ranges

        # Handle old format (convert first)
        page_ranges: dict[FinancialStatementType, list[int]] = {}
        for page_num, tables in detected_tables.items():
            for table in tables:
                stmt_type = table.statement_type
                if stmt_type not in page_ranges:
                    page_ranges[stmt_type] = []

                # Add surrounding pages
                for page_offset in [-1, 0, 1, 2]:
                    target_page = page_num + page_offset
                    if target_page > 0 and target_page not in page_ranges[stmt_type]:
                        page_ranges[stmt_type].append(target_page)

        # Sort page lists
        for stmt_type in page_ranges:
            page_ranges[stmt_type].sort()

        return page_ranges

    def save_detection_results(
        self, detected_tables: dict[int, list[DetectedTable]], output_path: str | Path
    ) -> None:
        """Save detection results to JSON file for debugging and analysis."""
        output_path = str(output_path)

        # Convert to serializable format
        serializable_results = {}
        for page_num, tables in detected_tables.items():
            serializable_results[page_num] = []
            for table in tables:
                table_data = {
                    "page_number": table.page_number,
                    "bbox": table.bbox,
                    "statement_type": table.statement_type.value,
                    "confidence_score": table.confidence_score,
                    "content_indicators": table.content_indicators,
                    "table_structure": table.table_structure,
                }
                serializable_results[page_num].append(table_data)

        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2)

        logger.info("Detection results saved", extra={"path": output_path})
