"""
Income Statement Schema for simple row-based financial data.

This schema handles income statements with straightforward structure:
- Account names with values across time periods
- Simple hierarchical grouping (Revenue, Expenses, Net Income)
- Consistent column structure across all rows
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .base_schema import BaseFinancialSchema, SimpleLineItem, FinancialStatementType, ExcelLayoutConfig, ExcelColumnMapping

class IncomeStatementLineItem(SimpleLineItem):
    """Income statement specific line item with additional fields."""
    account_category: Optional[str] = Field(description="Category: 'revenue', 'expense', 'income', 'other'", default="")
    is_calculated: bool = Field(description="Whether this is a calculated field (subtotal, etc.)", default=False)
    calculation_formula: Optional[str] = Field(description="Formula if this is calculated", default="")

class IncomeStatementSchema(BaseFinancialSchema):
    """
    Schema for Income Statements with simple row-based structure.
    
    Example structure:
    Revenue                     $ 10,918    $ 11,716    $ 9,714
    Cost of revenue               4,150       4,545      3,892
    Gross profit                  6,768       7,171      5,822
    Operating expenses:
      Research and development    2,829       2,376      1,797
      Sales and administrative    1,093         991        815
    Net income                  $ 2,796     $ 4,141    $ 3,047
    """
    
    document_type: FinancialStatementType = Field(default=FinancialStatementType.INCOME_STATEMENT)
    
    line_items: List[IncomeStatementLineItem] = Field(
        description="All line items in the income statement"
    )
    
    # Key financial metrics (automatically extracted)
    revenue_items: List[IncomeStatementLineItem] = Field(
        description="Revenue-related line items",
        default=[]
    )
    
    expense_items: List[IncomeStatementLineItem] = Field(
        description="Expense-related line items", 
        default=[]
    )
    
    net_income_items: List[IncomeStatementLineItem] = Field(
        description="Net income and profit-related items",
        default=[]
    )
    
    def get_revenue_total(self, period: str) -> Optional[str]:
        """Get total revenue for a specific period."""
        for item in self.revenue_items:
            if "revenue" in item.account_name.lower() and not item.is_calculated:
                return item.values.get(period)
        return None
    
    def get_net_income(self, period: str) -> Optional[str]:
        """Get net income for a specific period."""
        for item in self.net_income_items:
            if "net income" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_excel_layout_config(self) -> ExcelLayoutConfig:
        """Generate Excel layout configuration for income statement."""
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