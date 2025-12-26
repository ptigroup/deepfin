"""
Balance Sheet Schema for hierarchical asset/liability/equity structures.

This schema handles balance sheets with:
- Hierarchical account groupings (Assets -> Current Assets -> Cash)
- Indentation levels for sub-accounts
- Section totals and subtotals
- Assets = Liabilities + Equity structure
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .base_schema import BaseFinancialSchema, HierarchicalLineItem, FinancialStatementType, ExcelLayoutConfig, ExcelColumnMapping

class BalanceSheetAccount(HierarchicalLineItem):
    """Balance sheet account with hierarchical structure."""
    account_category: str = Field(description="Category: 'assets', 'liabilities', 'equity'")
    account_subcategory: Optional[str] = Field(description="Subcategory: 'current', 'non-current', etc.", default="")
    is_total: bool = Field(description="Whether this is a total/subtotal line", default=False)
    total_level: Optional[str] = Field(description="Level of total: 'subtotal', 'section_total', 'grand_total'", default="")

class BalanceSheetSchema(BaseFinancialSchema):
    """
    Schema for Balance Sheets with hierarchical structure.
    
    Example structure:
    ASSETS
      Current assets:
        Cash and cash equivalents    $ 1,000    $ 2,000
        Accounts receivable             500        600
        Inventory                       300        400
      Total current assets            1,800      3,000
      
      Non-current assets:
        Property, plant & equipment   5,000      4,500
      Total non-current assets        5,000      4,500
      
    Total assets                     $6,800     $7,500
    
    LIABILITIES AND EQUITY
      Current liabilities:            1,200      1,500
      Total liabilities               3,000      3,500
      
      Shareholders' equity:           3,800      4,000
    Total liabilities and equity     $6,800     $7,500
    """
    
    document_type: FinancialStatementType = Field(default=FinancialStatementType.BALANCE_SHEET)
    
    accounts: List[BalanceSheetAccount] = Field(
        description="All accounts in the balance sheet"
    )
    
    # Major sections
    asset_accounts: List[BalanceSheetAccount] = Field(
        description="Asset accounts",
        default=[]
    )
    
    liability_accounts: List[BalanceSheetAccount] = Field(
        description="Liability accounts",
        default=[]
    )
    
    equity_accounts: List[BalanceSheetAccount] = Field(
        description="Equity accounts", 
        default=[]
    )
    
    def get_total_assets(self, period: str) -> Optional[str]:
        """Get total assets for a specific period."""
        for account in self.asset_accounts:
            if account.is_total and "total assets" in account.account_name.lower():
                return account.values.get(period)
        return None
    
    def get_total_liabilities(self, period: str) -> Optional[str]:
        """Get total liabilities for a specific period.""" 
        for account in self.liability_accounts:
            if account.is_total and "total liabilities" in account.account_name.lower():
                return account.values.get(period)
        return None
    
    def get_total_equity(self, period: str) -> Optional[str]:
        """Get total equity for a specific period."""
        for account in self.equity_accounts:
            if account.is_total and ("total equity" in account.account_name.lower() or 
                                   "shareholders' equity" in account.account_name.lower()):
                return account.values.get(period)
        return None
    
    def get_excel_layout_config(self) -> ExcelLayoutConfig:
        """Generate Excel layout configuration for balance sheet."""
        # Build header rows
        header_rows = [self.company_name, self.document_title]
        if self.units_note:
            header_rows.append(self.units_note)
        
        # Build column mappings from reporting periods
        excel_mappings = []
        for i, period in enumerate(self.reporting_periods):
            excel_mappings.append(ExcelColumnMapping(
                excel_column_index=i + 2,  # Start from column B
                main_header=period,
                sub_header="",
                span_columns=1,
                data_type="currency"
            ))
        
        # Calculate table positioning
        header_count = len(header_rows)
        table_start_row = header_count + 2
        data_start_row = table_start_row + 1
        
        return ExcelLayoutConfig(
            header_rows=header_rows,
            column_mappings=excel_mappings,
            has_multi_level_headers=False,
            units_note_position="top",
            table_start_row=table_start_row,
            data_start_row=data_start_row
        )