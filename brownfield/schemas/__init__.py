"""
Financial Statement Schemas Registry.

This module provides a centralized registry for all financial statement schemas
and utilities for automatic document type detection and schema selection.
"""

from typing import Type, Dict, Optional
from .base_schema import BaseFinancialSchema, FinancialStatementType
from .income_statement_schema import IncomeStatementSchema
from .balance_sheet_schema import BalanceSheetSchema
from .cash_flow_schema import CashFlowSchema
from .shareholders_equity_schema import ShareholdersEquitySchema
from .comprehensive_income_schema import ComprehensiveIncomeSchema
from .document_detector import FinancialDocumentDetector

class FinancialSchemaRegistry:
    """Registry for managing financial statement schemas."""
    
    # Mapping of document types to their corresponding schema classes
    SCHEMA_MAP: Dict[FinancialStatementType, Type[BaseFinancialSchema]] = {
        FinancialStatementType.INCOME_STATEMENT: IncomeStatementSchema,
        FinancialStatementType.BALANCE_SHEET: BalanceSheetSchema,
        FinancialStatementType.CASH_FLOW: CashFlowSchema,
        FinancialStatementType.SHAREHOLDERS_EQUITY: ShareholdersEquitySchema,
        FinancialStatementType.COMPREHENSIVE_INCOME: ComprehensiveIncomeSchema,
    }
    
    def __init__(self):
        """Initialize the schema registry."""
        self.detector = FinancialDocumentDetector()
    
    def get_schema_class(self, document_type: FinancialStatementType) -> Optional[Type[BaseFinancialSchema]]:
        """
        Get the schema class for a specific document type.
        
        Args:
            document_type: The type of financial statement
            
        Returns:
            The corresponding schema class or None if not found
        """
        return self.SCHEMA_MAP.get(document_type)
    
    def detect_and_get_schema(self, extracted_text: str, document_title: str = "") -> tuple[Type[BaseFinancialSchema], FinancialStatementType, float]:
        """
        Automatically detect document type and return the appropriate schema class.
        
        Args:
            extracted_text: Raw text extracted from the document
            document_title: Optional document title/filename
            
        Returns:
            Tuple of (schema_class, detected_type, confidence_score)
        """
        detected_type, confidence = self.detector.detect_document_type(extracted_text, document_title)
        
        schema_class = self.get_schema_class(detected_type)
        
        # Fall back to income statement schema if detection fails
        if schema_class is None:
            schema_class = IncomeStatementSchema
            detected_type = FinancialStatementType.INCOME_STATEMENT
            confidence = 0.1  # Low confidence fallback
        
        return schema_class, detected_type, confidence
    
    def get_detection_details(self, extracted_text: str, document_title: str = "") -> Dict:
        """
        Get detailed information about document type detection.
        
        Args:
            extracted_text: Raw text extracted from the document
            document_title: Optional document title/filename
            
        Returns:
            Dictionary with detection details
        """
        return self.detector.get_detection_details(extracted_text, document_title)
    
    def list_available_schemas(self) -> Dict[str, str]:
        """
        List all available schemas and their purposes.
        
        Returns:
            Dictionary mapping document type names to schema descriptions
        """
        descriptions = {
            "income_statement": "Simple row-based structure for revenue, expenses, and net income",
            "balance_sheet": "Hierarchical structure for assets, liabilities, and equity",
            "cash_flow": "Activity-based structure for operating, investing, and financing activities",
            "shareholders_equity": "Complex multi-level header structure for equity transactions",
            "comprehensive_income": "Structure for net income plus other comprehensive income items"
        }
        return descriptions

# Create a global registry instance
schema_registry = FinancialSchemaRegistry()

# Convenience functions for easy access
def get_schema_for_document(extracted_text: str, document_title: str = ""):
    """
    Convenience function to get the appropriate schema class for a document.
    
    Returns:
        Tuple of (schema_class, document_type, confidence)
    """
    return schema_registry.detect_and_get_schema(extracted_text, document_title)

def get_schema_class(document_type: FinancialStatementType):
    """
    Convenience function to get schema class by document type.
    
    Returns:
        Schema class or None
    """
    return schema_registry.get_schema_class(document_type)

# Export all important classes and functions
__all__ = [
    # Base classes
    'BaseFinancialSchema',
    'FinancialStatementType',
    
    # Schema classes  
    'IncomeStatementSchema',
    'BalanceSheetSchema',
    'CashFlowSchema',
    'ShareholdersEquitySchema',
    'ComprehensiveIncomeSchema',
    
    # Registry and detection
    'FinancialSchemaRegistry',
    'FinancialDocumentDetector',
    'schema_registry',
    
    # Convenience functions
    'get_schema_for_document',
    'get_schema_class',
]