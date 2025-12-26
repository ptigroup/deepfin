"""
Document type auto-detection logic to choose the correct Pydantic schema.
Following CLAUDE.md universal rules - works with any financial table type.
"""

import re
from typing import Dict, List, Tuple
from schemas import SCHEMA_MAP, DOCUMENT_KEYWORDS


class DocumentTypeDetector:
    """Detects financial document type from extracted text to choose appropriate schema."""
    
    def __init__(self):
        self.keywords = DOCUMENT_KEYWORDS
        self.schema_map = SCHEMA_MAP
    
    def detect_document_type(self, extracted_text: str) -> Tuple[str, object]:
        """
        Analyze extracted text to determine document type and return appropriate schema.
        
        Args:
            extracted_text (str): Raw text from LLMWhisperer
            
        Returns:
            Tuple[str, object]: (document_type_name, pydantic_schema_class)
        """
        text_lower = extracted_text.lower()
        
        # Score each document type based on keyword presence
        scores = {}
        
        for doc_type, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences of each keyword
                matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
                score += matches
            
            scores[doc_type] = score
        
        # Find the document type with highest score
        best_match = max(scores.items(), key=lambda x: x[1])
        document_type = best_match[0]
        confidence_score = best_match[1]
        
        print(f"🔍 Document type detection scores: {scores}")
        print(f"✅ Detected document type: {document_type} (confidence: {confidence_score})")
        
        # Return document type and corresponding schema class
        schema_class = self.schema_map[document_type]
        return document_type, schema_class
    
    def get_document_specific_preamble(self, document_type: str) -> str:
        """
        Generate document-specific preamble for LLM prompt.
        
        Args:
            document_type (str): Detected document type
            
        Returns:
            str: Tailored preamble for the specific document type
        """
        preambles = {
            "income_statement": (
                "You are analyzing an income statement or profit & loss document. "
                "Extract all revenue, expense, and profit/loss line items with their amounts. "
                "Preserve exact account names including indentation and formatting. "
                "Include all financial data rows in chronological order."
            ),
            "balance_sheet": (
                "You are analyzing a balance sheet document. "
                "Extract all assets, liabilities, and equity line items with their amounts. "
                "Preserve exact account names including indentation and formatting. "
                "Include all financial data rows maintaining the balance sheet structure."
            ),
            "cash_flow": (
                "You are analyzing a cash flow statement document. "
                "Extract all operating, investing, and financing cash flow items with their amounts. "
                "Preserve exact account names including indentation and formatting. "
                "Include all cash flow line items in their respective sections."
            ),
            "comprehensive_income": (
                "You are analyzing a comprehensive income statement document. "
                "Extract all comprehensive income components including other comprehensive income items. "
                "Preserve exact account names including indentation and formatting. "
                "Include all comprehensive income line items in order."
            ),
            "shareholder_equity": (
                "You are analyzing a shareholder equity or stockholders' equity statement. "
                "Extract all equity transactions, retained earnings, and capital changes with amounts. "
                "Preserve exact account names including indentation and formatting. "
                "Include all equity-related line items and transactions."
            )
        }
        
        return preambles.get(document_type, 
                           "You are analyzing a financial document. Extract all financial line items with their amounts.")
    
    def validate_detection(self, document_type: str, extracted_text: str) -> bool:
        """
        Validate that the detected document type makes sense given the content.
        
        Args:
            document_type (str): Detected document type
            extracted_text (str): Raw text from document
            
        Returns:
            bool: True if detection seems valid, False otherwise
        """
        text_lower = extracted_text.lower()
        
        # Check for strong indicators of the detected type
        strong_indicators = {
            "income_statement": ["revenue", "net income", "gross profit"],
            "balance_sheet": ["total assets", "total liabilities", "shareholders' equity"], 
            "cash_flow": ["cash flows from operating", "cash flows from investing"],
            "comprehensive_income": ["comprehensive income", "other comprehensive"],
            "shareholder_equity": ["retained earnings", "common stock", "additional paid-in"]
        }
        
        indicators = strong_indicators.get(document_type, [])
        found_indicators = sum(1 for indicator in indicators if indicator in text_lower)
        
        # Consider valid if at least one strong indicator is found
        is_valid = found_indicators > 0
        
        if not is_valid:
            print(f"⚠️  Document type validation warning: {document_type} may not be correct")
            print(f"   Expected indicators: {indicators}")
            print(f"   Found indicators: {found_indicators}")
        
        return is_valid
    
    def get_fallback_schema(self):
        """
        Return a generic schema if document type detection fails.
        
        Returns:
            object: Generic schema class for unknown document types
        """
        # Default to income statement schema as it's most flexible
        return self.schema_map["income_statement"]


def detect_and_validate_document(extracted_text: str) -> Tuple[str, object, str]:
    """
    Main function to detect document type, validate it, and return schema with preamble.
    
    Args:
        extracted_text (str): Raw text from LLMWhisperer
        
    Returns:
        Tuple[str, object, str]: (document_type, schema_class, preamble)
    """
    detector = DocumentTypeDetector()
    
    # Detect document type
    document_type, schema_class = detector.detect_document_type(extracted_text)
    
    # Validate detection
    is_valid = detector.validate_detection(document_type, extracted_text)
    
    if not is_valid:
        print("⚠️  Using detected type anyway, but results may vary")
    
    # Get appropriate preamble
    preamble = detector.get_document_specific_preamble(document_type)
    
    return document_type, schema_class, preamble