"""
Base schema classes and common fields for financial statement processing.
All specific financial statement schemas should inherit from these base classes.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FinancialStatementType(str, Enum):
    """Supported financial statement types."""

    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    CASH_FLOW = "cash_flow"
    COMPREHENSIVE_INCOME = "comprehensive_income"
    UNKNOWN = "unknown"


class ExcelColumnMapping(BaseModel):
    """Defines how a column should appear in Excel."""

    excel_column_index: int = Field(description="Excel column position (1=A, 2=B, etc.)")
    main_header: str = Field(description="Main column header text")
    sub_header: str | None = Field(description="Sub-header text", default="")
    span_columns: int = Field(description="How many Excel columns this header spans", default=1)
    data_type: str = Field(
        description="Data type for formatting (text, currency, number, percentage)", default="text"
    )
    merge_with_next: bool = Field(
        description="Whether to merge with next column for main header", default=False
    )


class ExcelLayoutConfig(BaseModel):
    """Defines Excel layout configuration for a financial statement."""

    header_rows: list[str] = Field(description="Header rows (company name, doc title, units, etc.)")
    column_mappings: list[ExcelColumnMapping] = Field(
        description="Column definitions and formatting"
    )
    has_multi_level_headers: bool = Field(
        description="Whether this has main + sub header rows", default=False
    )
    units_note_position: str = Field(description="Where to place units note", default="top")
    table_start_row: int = Field(description="Excel row where table headers start", default=1)
    data_start_row: int = Field(description="Excel row where data starts", default=1)


class BaseFinancialSchema(BaseModel):
    """Base schema that all financial statements inherit from."""

    company_name: str = Field(description="Name of the company")
    document_title: str = Field(description="Title of the financial statement")
    document_type: FinancialStatementType = Field(description="Type of financial statement")
    reporting_periods: list[str] = Field(description="Time periods covered (years, quarters, etc.)")
    units_note: str | None = Field(
        description="Units note (e.g., 'In millions, except per share data')", default=""
    )
    consolidation_summary: dict[str, Any] | None = Field(
        description="Summary of account consolidations for transparency", default=None
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True
        extra = "allow"  # Allow extra fields for consolidation metadata

    def get_excel_layout_config(self) -> ExcelLayoutConfig:
        """
        Generate Excel layout configuration from schema data.
        Each schema should override this method for specific formatting.
        """
        # Default implementation for simple schemas
        header_rows = [self.company_name, self.document_title]
        if self.units_note:
            header_rows.append(self.units_note)

        return ExcelLayoutConfig(
            header_rows=header_rows,
            column_mappings=[],
            has_multi_level_headers=False,
            units_note_position="top",
            table_start_row=len(header_rows) + 2,
            data_start_row=len(header_rows) + 3,
        )


class BaseLineItem(BaseModel):
    """Base class for financial line items."""

    account_name: str = Field(description="Name of the account or line item")
    indent_level: int = Field(
        description="Indentation level for hierarchy (0=main level)", default=0
    )
    is_section_header: bool = Field(description="Whether this is a section header", default=False)
    parent_section: str | None = Field(
        description="Name of parent section if applicable", default=""
    )


class SimpleLineItem(BaseLineItem):
    """Simple line item with values across periods (for Income Statement, Cash Flow)."""

    values: dict[str, str] = Field(description="Values for each reporting period")


class HierarchicalLineItem(BaseLineItem):
    """Hierarchical line item for Balance Sheet with sub-accounts."""

    values: dict[str, str] = Field(description="Values for each reporting period")
    sub_items: list["HierarchicalLineItem"] | None = Field(
        description="Sub-items under this account", default=[]
    )


# Enable forward references for self-referencing models
HierarchicalLineItem.model_rebuild()


class ColumnHeader(BaseModel):
    """Represents a column header in complex table structures."""

    main_header: str = Field(description="Main column header")
    sub_header: str | None = Field(description="Sub-header under the main header", default="")
    position: int = Field(description="Column position (0-based)")


class MetadataInfo(BaseModel):
    """Extraction metadata."""

    extraction_method: str = Field(description="Method used for extraction")
    extraction_timestamp: str = Field(description="When the extraction was performed")
    schema_version: str = Field(description="Version of the schema used", default="1.0")
    processing_notes: list[str] = Field(description="Any processing notes or warnings", default=[])
