"""
Document Type Detection System for Financial Statements.

This module analyzes extracted text to automatically determine which financial statement
type is being processed with confidence scoring for validation.

Ported from brownfield/schemas/document_detector.py for hybrid architecture.
"""

import re
from enum import Enum


class FinancialStatementType(str, Enum):
    """Supported financial statement types."""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    CASH_FLOW = "cash_flow"
    COMPREHENSIVE_INCOME = "comprehensive_income"
    UNKNOWN = "unknown"


class FinancialDocumentDetector:
    """Analyzes extracted text to determine financial statement type with confidence scoring."""

    # Keywords that strongly indicate specific document types
    STRONG_INDICATORS = {
        FinancialStatementType.INCOME_STATEMENT: [
            "net income", "revenue", "cost of revenue", "operating expenses",
            "gross profit", "net earnings", "earnings per share", "diluted shares"
        ],
        FinancialStatementType.BALANCE_SHEET: [
            "total assets", "current assets", "total liabilities", "shareholders' equity",
            "cash and cash equivalents", "accounts receivable", "inventory",
            "retained earnings", "common stock"
        ],
        FinancialStatementType.CASH_FLOW: [
            "cash flows from operating activities", "cash flows from investing activities",
            "cash flows from financing activities", "net cash provided by",
            "depreciation and amortization", "capital expenditures", "free cash flow"
        ],
        FinancialStatementType.SHAREHOLDERS_EQUITY: [
            "common stock outstanding", "shares", "additional paid-in capital",
            "treasury stock", "accumulated other comprehensive income",
            "retained earnings", "stockholders' equity", "shareholders' equity"
        ],
        FinancialStatementType.COMPREHENSIVE_INCOME: [
            "comprehensive income", "other comprehensive income", "foreign currency translation",
            "unrealized gains", "unrealized losses", "total comprehensive income"
        ]
    }

    # Title patterns that indicate document type
    TITLE_PATTERNS = {
        FinancialStatementType.INCOME_STATEMENT: [
            r"statement.*of.*income", r"statement.*of.*operations", r"statement.*of.*earnings",
            r"income.*statement", r"profit.*and.*loss", r"p\s*&\s*l",
            r"consolidated.*statements?.*of.*income"
        ],
        FinancialStatementType.BALANCE_SHEET: [
            r"balance.*sheet", r"statement.*of.*financial.*position",
            r"consolidated.*balance.*sheet"
        ],
        FinancialStatementType.CASH_FLOW: [
            r"statement.*of.*cash.*flows", r"cash.*flow.*statement",
            r"consolidated.*statements?.*of.*cash.*flows"
        ],
        FinancialStatementType.SHAREHOLDERS_EQUITY: [
            r"statement.*of.*shareholders.*equity", r"statement.*of.*stockholders.*equity",
            r"equity.*statement", r"statement.*of.*equity"
        ],
        FinancialStatementType.COMPREHENSIVE_INCOME: [
            r"statement.*of.*comprehensive.*income", r"comprehensive.*income.*statement"
        ]
    }

    # Structural patterns that suggest specific document types
    STRUCTURE_PATTERNS = {
        FinancialStatementType.SHAREHOLDERS_EQUITY: [
            r"shares\s*\|\s*amount",  # Multi-column headers
            r"common stock outstanding.*shares.*amount",
            r"balances.*shares.*amount.*capital"
        ],
        FinancialStatementType.CASH_FLOW: [
            r"operating activities.*investing activities.*financing activities",
            r"net cash.*operating.*investing.*financing"
        ]
    }

    # Negative indicators that suggest it's NOT the target type (e.g., summary pages)
    NEGATIVE_INDICATORS = {
        FinancialStatementType.INCOME_STATEMENT: [
            r"fiscal\s+year.*summary",  # Summary tables, not full statements
            r"selected\s+financial\s+data",
            r"financial\s+highlights"
        ]
    }

    def __init__(self):
        """Initialize the document detector."""
        pass

    def detect_document_type(self, extracted_text: str, document_title: str = "") -> tuple[FinancialStatementType, float]:
        """
        Detect the financial statement type from extracted text with confidence scoring.

        Args:
            extracted_text: Raw text extracted from the document
            document_title: Optional document title/filename

        Returns:
            Tuple of (detected_type, confidence_score)

        Confidence Scoring:
            - Title patterns: +0.4 (filename), +0.3 (document header)
            - Keywords: +0.4 × (matched / total)
            - Structure: +0.5 per pattern
            - Negative indicators: -0.3 per pattern
            - Minimum threshold: 0.2 (below = UNKNOWN)
        """
        text_lower = extracted_text.lower()
        title_lower = document_title.lower()

        scores = dict.fromkeys(FinancialStatementType, 0.0)

        # Check title patterns (high weight)
        for doc_type, patterns in self.TITLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    scores[doc_type] += 0.4
                if re.search(pattern, text_lower[:500]):  # Check beginning of document
                    scores[doc_type] += 0.3

        # Check strong keyword indicators (medium weight)
        for doc_type, keywords in self.STRONG_INDICATORS.items():
            keyword_count = 0
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_count += 1

            # Normalize score based on keyword presence
            scores[doc_type] += (keyword_count / len(keywords)) * 0.4

        # Check structural patterns (high weight for specific types)
        for doc_type, patterns in self.STRUCTURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    scores[doc_type] += 0.5

        # Check negative indicators (penalty for summary pages, etc.)
        for doc_type, patterns in self.NEGATIVE_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    scores[doc_type] -= 0.3

        # Find the highest scoring type
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        # If confidence is too low, return UNKNOWN
        if confidence < 0.2:
            return FinancialStatementType.UNKNOWN, confidence

        return best_type, confidence

    def get_detection_details(self, extracted_text: str, document_title: str = "") -> dict:
        """
        Get detailed detection information for debugging and analysis.

        Returns:
            Dictionary with detection details and scores for all types
        """
        text_lower = extracted_text.lower()
        title_lower = document_title.lower()

        details = {
            "document_title": document_title,
            "text_length": len(extracted_text),
            "scores": {},
            "matched_keywords": {},
            "matched_patterns": {},
            "negative_matches": {},
            "detected_type": None,
            "confidence": 0.0
        }

        scores = dict.fromkeys(FinancialStatementType, 0.0)
        matched_keywords = {doc_type: [] for doc_type in FinancialStatementType}
        matched_patterns = {doc_type: [] for doc_type in FinancialStatementType}
        negative_matches = {doc_type: [] for doc_type in FinancialStatementType}

        # Title pattern matching
        for doc_type, patterns in self.TITLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    scores[doc_type] += 0.4
                    matched_patterns[doc_type].append(f"title:{pattern}")
                if re.search(pattern, text_lower[:500]):
                    scores[doc_type] += 0.3
                    matched_patterns[doc_type].append(f"text_start:{pattern}")

        # Keyword matching
        for doc_type, keywords in self.STRONG_INDICATORS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched_keywords[doc_type].append(keyword)

            keyword_score = (len(matched_keywords[doc_type]) / len(keywords)) * 0.4
            scores[doc_type] += keyword_score

        # Structure pattern matching
        for doc_type, patterns in self.STRUCTURE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    scores[doc_type] += 0.5
                    matched_patterns[doc_type].append(f"structure:{pattern}")

        # Negative indicator matching
        for doc_type, patterns in self.NEGATIVE_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    scores[doc_type] -= 0.3
                    negative_matches[doc_type].append(pattern)

        details["scores"] = scores
        details["matched_keywords"] = matched_keywords
        details["matched_patterns"] = matched_patterns
        details["negative_matches"] = negative_matches

        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        details["detected_type"] = best_type if confidence >= 0.2 else FinancialStatementType.UNKNOWN
        details["confidence"] = confidence

        return details
