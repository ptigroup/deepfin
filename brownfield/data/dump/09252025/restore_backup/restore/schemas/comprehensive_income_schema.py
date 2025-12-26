"""
Comprehensive Income Schema for statements with other comprehensive income items.

This schema handles comprehensive income statements with:
- Net income from income statement
- Other comprehensive income items (foreign currency, unrealized gains/losses)
- Total comprehensive income calculations
- Similar structure to income statements but with additional OCI sections
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .base_schema import BaseFinancialSchema, SimpleLineItem, FinancialStatementType, ExcelLayoutConfig, ExcelColumnMapping

class ComprehensiveIncomeLineItem(SimpleLineItem):
    """Comprehensive income line item with OCI classification."""
    item_category: str = Field(description="Category: 'net_income', 'oci', 'total_comprehensive'")
    oci_type: Optional[str] = Field(description="OCI type: 'foreign_currency', 'unrealized_gains', 'pension', 'other'", default="")
    is_total_line: bool = Field(description="Whether this is a total or subtotal line", default=False)
    related_to_tax: bool = Field(description="Whether this item relates to tax effects", default=False)

class ComprehensiveIncomeSchema(BaseFinancialSchema):
    """
    Schema for Comprehensive Income Statements.
    
    Example structure:
    Net income                                    $ 2,796    $ 4,141
    Other comprehensive income:
      Foreign currency translation adjustments      (45)        120
      Unrealized gains on securities                 25          15
      Tax effect on other comprehensive income        5          (8)
    Other comprehensive income, net of tax          (15)        127
    Total comprehensive income                   $ 2,781    $ 4,268
    """
    
    document_type: FinancialStatementType = Field(default=FinancialStatementType.COMPREHENSIVE_INCOME)
    
    line_items: List[ComprehensiveIncomeLineItem] = Field(
        description="All line items in the comprehensive income statement"
    )
    
    # Net income section
    net_income_items: List[ComprehensiveIncomeLineItem] = Field(
        description="Net income line items (from income statement)",
        default=[]
    )
    
    # Other comprehensive income sections
    oci_items: List[ComprehensiveIncomeLineItem] = Field(
        description="Other comprehensive income items",
        default=[]
    )
    
    foreign_currency_items: List[ComprehensiveIncomeLineItem] = Field(
        description="Foreign currency translation items",
        default=[]
    )
    
    unrealized_gains_items: List[ComprehensiveIncomeLineItem] = Field(
        description="Unrealized gains/losses on securities",
        default=[]
    )
    
    pension_items: List[ComprehensiveIncomeLineItem] = Field(
        description="Pension and benefit plan adjustments",
        default=[]
    )
    
    # Total comprehensive income
    total_comprehensive_items: List[ComprehensiveIncomeLineItem] = Field(
        description="Total comprehensive income items",
        default=[]
    )
    
    def get_net_income(self, period: str) -> Optional[str]:
        """Get net income for a specific period."""
        for item in self.net_income_items:
            if "net income" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_total_oci(self, period: str) -> Optional[str]:
        """Get total other comprehensive income for a specific period."""
        for item in self.oci_items:
            if item.is_total_line and "other comprehensive income" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_total_comprehensive_income(self, period: str) -> Optional[str]:
        """Get total comprehensive income for a specific period."""
        for item in self.total_comprehensive_items:
            if "total comprehensive income" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_excel_layout_config(self) -> ExcelLayoutConfig:
        """Generate Excel layout configuration for comprehensive income statement."""
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