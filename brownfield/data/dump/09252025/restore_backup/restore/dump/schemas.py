"""
Pydantic schemas for different financial document types.
Based on GitHub repo approach and designed to work with any financial table structure.
"""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field


# Line Item Models (reusable components)
class FinancialLineItem(BaseModel):
    """Base model for any financial line item with account name and values."""
    account_name: str = Field(description="Account or item name exactly as shown, including indentation")
    current_period: Optional[Union[float, str]] = Field(description="Current period value, preserve original formatting")
    previous_period: Optional[Union[float, str]] = Field(description="Previous period value, preserve original formatting")
    third_period: Optional[Union[float, str]] = Field(description="Third period value if present, preserve original formatting")


# Income Statement Schema
class IncomeStatementItem(BaseModel):
    """Individual line item from income statement."""
    account_name: str = Field(description="Revenue, expense, or income account name exactly as shown with indentation")
    current_year: Optional[Union[float, str]] = Field(description="Most recent year amount, preserve formatting")
    previous_year: Optional[Union[float, str]] = Field(description="Previous year amount, preserve formatting") 
    third_year: Optional[Union[float, str]] = Field(description="Third year amount if present, preserve formatting")


class IncomeStatement(BaseModel):
    """Complete income statement with all line items."""
    document_title: str = Field(description="Title of the income statement document")
    reporting_periods: List[str] = Field(description="List of reporting periods/years from column headers")
    line_items: List[IncomeStatementItem] = Field(description="All income statement line items in order")


# Balance Sheet Schema  
class BalanceSheetItem(BaseModel):
    """Individual line item from balance sheet."""
    account_name: str = Field(description="Asset, liability, or equity account name exactly as shown with indentation")
    current_period: Optional[Union[float, str]] = Field(description="Most recent period amount, preserve formatting")
    previous_period: Optional[Union[float, str]] = Field(description="Previous period amount, preserve formatting")


class BalanceSheet(BaseModel):
    """Complete balance sheet with all line items."""
    document_title: str = Field(description="Title of the balance sheet document")
    reporting_periods: List[str] = Field(description="List of reporting periods/dates from column headers")
    line_items: List[BalanceSheetItem] = Field(description="All balance sheet line items in order")


# Cash Flow Statement Schema
class CashFlowItem(BaseModel):
    """Individual line item from cash flow statement."""
    account_name: str = Field(description="Cash flow item name exactly as shown with indentation")
    current_period: Optional[Union[float, str]] = Field(description="Most recent period amount, preserve formatting")
    previous_period: Optional[Union[float, str]] = Field(description="Previous period amount, preserve formatting")
    third_period: Optional[Union[float, str]] = Field(description="Third period amount if present, preserve formatting")


class CashFlowStatement(BaseModel):
    """Complete cash flow statement with all line items."""
    document_title: str = Field(description="Title of the cash flow statement document")
    reporting_periods: List[str] = Field(description="List of reporting periods/years from column headers")
    line_items: List[CashFlowItem] = Field(description="All cash flow statement line items in order")


# Comprehensive Income Schema
class ComprehensiveIncomeItem(BaseModel):
    """Individual line item from comprehensive income statement.""" 
    account_name: str = Field(description="Comprehensive income item name exactly as shown with indentation")
    current_period: Optional[Union[float, str]] = Field(description="Most recent period amount, preserve formatting")
    previous_period: Optional[Union[float, str]] = Field(description="Previous period amount, preserve formatting")
    third_period: Optional[Union[float, str]] = Field(description="Third period amount if present, preserve formatting")


class ComprehensiveIncome(BaseModel):
    """Complete comprehensive income statement with all line items."""
    document_title: str = Field(description="Title of the comprehensive income statement document")
    reporting_periods: List[str] = Field(description="List of reporting periods/years from column headers")
    line_items: List[ComprehensiveIncomeItem] = Field(description="All comprehensive income line items in order")


# Shareholder Equity Schema
class ShareholderEquityItem(BaseModel):
    """Individual line item from shareholder equity statement."""
    account_name: str = Field(description="Equity account or transaction name exactly as shown with indentation")
    current_period: Optional[Union[float, str]] = Field(description="Most recent period amount, preserve formatting")
    previous_period: Optional[Union[float, str]] = Field(description="Previous period amount, preserve formatting")
    third_period: Optional[Union[float, str]] = Field(description="Third period amount if present, preserve formatting")


class ShareholderEquity(BaseModel):
    """Complete shareholder equity statement with all line items."""
    document_title: str = Field(description="Title of the shareholder equity statement document") 
    reporting_periods: List[str] = Field(description="List of reporting periods/years from column headers")
    line_items: List[ShareholderEquityItem] = Field(description="All shareholder equity line items in order")


# Document type detection helpers
SCHEMA_MAP = {
    "income_statement": IncomeStatement,
    "balance_sheet": BalanceSheet, 
    "cash_flow": CashFlowStatement,
    "comprehensive_income": ComprehensiveIncome,
    "shareholder_equity": ShareholderEquity
}

DOCUMENT_KEYWORDS = {
    "income_statement": ["income", "revenue", "profit", "earnings", "operations"],
    "balance_sheet": ["assets", "liabilities", "balance", "total assets"],
    "cash_flow": ["cash flow", "operating", "investing", "financing", "cash"],
    "comprehensive_income": ["comprehensive", "other comprehensive", "total comprehensive"],
    "shareholder_equity": ["shareholders", "stockholders", "stockholders' equity", "retained earnings", "capital", "common stock", "paid-in capital"]
}