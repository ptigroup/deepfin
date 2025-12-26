"""
Shareholders' Equity Schema for complex multi-level header table structures.

This schema handles the unique structure of shareholders' equity statements where:
- Main headers span multiple sub-columns (e.g., "Common Stock Outstanding" has "Shares" and "Amount")
- Data is organized in a complex table with hierarchical column headers
- Each row represents a transaction or balance with values across multiple column categories
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .base_schema import BaseFinancialSchema, ColumnHeader, FinancialStatementType, ExcelLayoutConfig, ExcelColumnMapping

class ShareholdersEquityColumn(BaseModel):
    """Represents a column in the shareholders' equity table with its header structure."""
    main_header: str = Field(description="Main column header (e.g., 'Common Stock Outstanding')")
    sub_header: str = Field(description="Sub-header that explains what this column contains (e.g., 'Shares', 'Amount')")
    column_index: int = Field(description="Position in the table (0-based)")
    data_type: str = Field(description="Type of data in this column (shares, currency, percentage, etc.)", default="text")

class ShareholdersEquityRow(BaseModel):
    """Represents a row in the shareholders' equity statement."""
    transaction_description: str = Field(description="Description of the transaction or balance")
    row_type: str = Field(description="Type of row: 'balance', 'transaction', 'subtotal', 'total'", default="transaction")
    date_reference: Optional[str] = Field(description="Date reference if applicable (e.g., 'January 29, 2017')", default="")
    column_values: Dict[str, str] = Field(description="Values for each column, keyed by 'main_header:sub_header'")

class ShareholdersEquitySchema(BaseFinancialSchema):
    """
    Specialized schema for Shareholders' Equity statements.
    
    Handles complex table structures like:
    
    | Transaction | Common Stock Outstanding | Additional | Treasury | Accumulated Other | Retained | Total |
    |            | Shares  | Amount        | Paid-in   | Stock    | Comprehensive     | Earnings | Equity |
    |------------|---------|---------------|-----------|----------|-------------------|----------|-------- |
    | Balance... | 585     | $ 1          | $ 4,708   | $(5,039) | $ (16)           | $ 6,108  | $ 5,762|
    """
    
    document_type: FinancialStatementType = Field(default=FinancialStatementType.SHAREHOLDERS_EQUITY)
    
    # Column structure definition
    column_headers: List[ShareholdersEquityColumn] = Field(
        description="Definition of all columns including main headers and sub-headers"
    )
    
    # Data rows
    equity_rows: List[ShareholdersEquityRow] = Field(
        description="All rows in the shareholders' equity statement"
    )
    
    # Balance information
    opening_balances: List[ShareholdersEquityRow] = Field(
        description="Opening balance rows (e.g., 'Balances, January 29, 2017')",
        default=[]
    )
    
    closing_balances: List[ShareholdersEquityRow] = Field(
        description="Closing balance rows (e.g., 'Balances, January 26, 2020')", 
        default=[]
    )
    
    # Additional metadata
    fiscal_years_covered: List[str] = Field(
        description="Fiscal years covered in this statement",
        default=[]
    )
    
    def get_column_by_headers(self, main_header: str, sub_header: str) -> Optional[ShareholdersEquityColumn]:
        """Helper method to find a column by its main and sub headers."""
        for col in self.column_headers:
            if col.main_header == main_header and col.sub_header == sub_header:
                return col
        return None
    
    def get_balance_rows(self, balance_type: str = "balance") -> List[ShareholdersEquityRow]:
        """Helper method to get all balance rows."""
        return [row for row in self.equity_rows if row.row_type == balance_type]
    
    def get_transaction_rows(self) -> List[ShareholdersEquityRow]:
        """Helper method to get all transaction rows."""
        return [row for row in self.equity_rows if row.row_type == "transaction"]
    
    def get_excel_layout_config(self) -> ExcelLayoutConfig:
        """Generate Excel layout configuration for shareholders' equity table."""
        # NO header rows - start directly with the table
        header_rows = []
        
        # Convert column headers to Excel mappings
        excel_mappings = []
        
        for i, col in enumerate(self.column_headers):
            # Determine if this column should span multiple Excel columns
            span_columns = 1
            merge_with_next = False
            
            # Handle "Common Stock Outstanding" which spans Shares and Amount columns
            if col.main_header == "Common Stock Outstanding" and col.sub_header == "Shares":
                # This is the first column of the pair, it should merge with next for main header
                merge_with_next = True
                span_columns = 1  # Each sub-column takes 1 Excel column
            elif col.main_header == "Common Stock Outstanding" and col.sub_header == "Amount":
                # This is the second column of the pair
                span_columns = 1
                merge_with_next = False
            
            excel_mappings.append(ExcelColumnMapping(
                excel_column_index=i + 2,  # Start from column B (A is for transaction descriptions)
                main_header=col.main_header,
                sub_header=col.sub_header,
                span_columns=span_columns,
                data_type=col.data_type,
                merge_with_next=merge_with_next
            ))
        
        # Calculate table positioning - start at row 1 since no headers
        table_start_row = 1
        data_start_row = table_start_row + 2 if len(excel_mappings) > 0 and any(m.sub_header for m in excel_mappings) else table_start_row + 1
        
        return ExcelLayoutConfig(
            header_rows=header_rows,  # Empty - no title headers
            column_mappings=excel_mappings,
            has_multi_level_headers=True,  # Main headers + sub headers
            units_note_position="bottom",  # Units note at the bottom
            table_start_row=table_start_row,
            data_start_row=data_start_row
        )

class ShareholdersEquityColumnMapping(BaseModel):
    """Helper class to map complex column structures from raw text."""
    raw_main_headers: List[str] = Field(description="Main headers as extracted from raw text")
    raw_sub_headers: List[str] = Field(description="Sub-headers as extracted from raw text") 
    column_mappings: List[ShareholdersEquityColumn] = Field(description="Processed column definitions")
    
    @classmethod
    def create_from_raw_headers(cls, main_headers: List[str], sub_headers: List[str]) -> "ShareholdersEquityColumnMapping":
        """Create column mapping from raw header data."""
        mappings = []
        
        # Handle cases where main headers span multiple sub-headers
        col_index = 0
        for i, main_header in enumerate(main_headers):
            if i < len(sub_headers):
                sub_header = sub_headers[i]
                mappings.append(ShareholdersEquityColumn(
                    main_header=main_header,
                    sub_header=sub_header,
                    column_index=col_index,
                    data_type="currency" if "$" in sub_header or "Amount" in sub_header else "number"
                ))
                col_index += 1
        
        return cls(
            raw_main_headers=main_headers,
            raw_sub_headers=sub_headers,
            column_mappings=mappings
        )