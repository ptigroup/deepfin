"""
Cash Flow Schema for activity-based cash flow statements.

This schema handles cash flow statements with:
- Activity-based grouping (Operating, Investing, Financing)
- Mixed positive/negative cash flows
- Reconciliation structure (beginning cash + activities = ending cash)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .base_schema import BaseFinancialSchema, SimpleLineItem, FinancialStatementType, ExcelLayoutConfig, ExcelColumnMapping

class CashFlowActivity(str):
    """Cash flow activity types."""
    OPERATING = "operating"
    INVESTING = "investing" 
    FINANCING = "financing"
    SUPPLEMENTAL = "supplemental"

class CashFlowLineItem(SimpleLineItem):
    """Cash flow line item with activity classification."""
    activity_type: str = Field(description="Activity type: operating, investing, financing, supplemental")
    cash_flow_direction: str = Field(description="Direction: 'inflow', 'outflow', 'neutral'", default="neutral")
    is_subtotal: bool = Field(description="Whether this is a subtotal for an activity", default=False)
    is_reconciliation: bool = Field(description="Whether this is part of cash reconciliation", default=False)

class CashFlowSchema(BaseFinancialSchema):
    """
    Schema for Cash Flow Statements with activity-based structure.
    
    Example structure:
    Operating Activities:
      Net income                           $ 2,796    $ 4,141
      Adjustments to reconcile:
        Depreciation and amortization        1,098      1,200
        Stock-based compensation              845        561
      Changes in operating assets:
        Accounts receivable                  (150)       200
    Net cash from operating activities      4,589      6,102
    
    Investing Activities:
      Capital expenditures                 (1,100)    (1,500)
    Net cash from investing activities     (1,100)    (1,500)
    
    Financing Activities:
      Share repurchases                      (900)    (1,579)
      Dividends paid                         (390)      (371)
    Net cash from financing activities     (1,290)    (1,950)
    
    Net change in cash                      2,199      2,652
    Cash at beginning of period            10,896      8,244
    Cash at end of period                 $13,095    $10,896
    """
    
    document_type: FinancialStatementType = Field(default=FinancialStatementType.CASH_FLOW)
    
    line_items: List[CashFlowLineItem] = Field(
        description="All line items in the cash flow statement"
    )
    
    # Activity sections
    operating_activities: List[CashFlowLineItem] = Field(
        description="Operating activity line items",
        default=[]
    )
    
    investing_activities: List[CashFlowLineItem] = Field(
        description="Investing activity line items",
        default=[]
    )
    
    financing_activities: List[CashFlowLineItem] = Field(
        description="Financing activity line items",
        default=[]
    )
    
    supplemental_info: List[CashFlowLineItem] = Field(
        description="Supplemental cash flow information",
        default=[]
    )
    
    # Reconciliation items
    beginning_cash: List[CashFlowLineItem] = Field(
        description="Beginning cash balance items",
        default=[]
    )
    
    ending_cash: List[CashFlowLineItem] = Field(
        description="Ending cash balance items", 
        default=[]
    )
    
    def get_net_cash_from_operations(self, period: str) -> Optional[str]:
        """Get net cash from operating activities for a specific period."""
        for item in self.operating_activities:
            if item.is_subtotal and "operating activities" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_net_cash_from_investing(self, period: str) -> Optional[str]:
        """Get net cash from investing activities for a specific period."""
        for item in self.investing_activities:
            if item.is_subtotal and "investing activities" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_net_cash_from_financing(self, period: str) -> Optional[str]:
        """Get net cash from financing activities for a specific period."""
        for item in self.financing_activities:
            if item.is_subtotal and "financing activities" in item.account_name.lower():
                return item.values.get(period)
        return None
    
    def get_excel_layout_config(self) -> ExcelLayoutConfig:
        """Generate Excel layout configuration for cash flow statement."""
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