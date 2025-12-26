#!/usr/bin/env python3
"""
Direct Balance Sheet Parser

Parses balance sheet raw text directly from LLMWhisperer output,
bypassing LLM interpretation to ensure 100% data accuracy and preserve
table structure including indentation levels.
"""

import re
from typing import List, Dict, Tuple, Optional
from schemas.balance_sheet_schema import BalanceSheetSchema, BalanceSheetAccount
from pipeline_logger import logger

def parse_balance_sheet_directly(raw_text_file_path: str) -> BalanceSheetSchema:
    """
    Parse balance sheet directly from raw LLMWhisperer text.
    
    Args:
        raw_text_file_path: Path to the raw text file
        
    Returns:
        BalanceSheetSchema: Populated schema instance
    """
    logger.debug("Using direct raw text parsing for reliable table structure preservation")
    
    with open(raw_text_file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Extract company info and metadata
    company_name = extract_company_name(raw_text)
    document_title = extract_document_title(raw_text)
    units_note = extract_units_note(raw_text)
    reporting_periods = extract_reporting_periods(raw_text)
    
    # Parse the table data
    line_items = parse_table_data(raw_text, reporting_periods)
    
    # Categorize line items
    asset_items = [item for item in line_items if item.account_category == "asset"]
    liability_items = [item for item in line_items if item.account_category == "liability"]
    equity_items = [item for item in line_items if item.account_category == "equity"]
    
    logger.debug(f"📊 Extracted {len(line_items)} line items")
    logger.debug(f"🏢 Found {len(asset_items)} asset items")
    logger.debug(f"💳 Found {len(liability_items)} liability items") 
    logger.debug(f"📈 Found {len(equity_items)} equity items")
    
    return BalanceSheetSchema(
        company_name=company_name,
        document_title=document_title,
        document_type="balance_sheet",
        reporting_periods=reporting_periods,
        units_note=units_note,
        accounts=line_items,
        asset_accounts=asset_items,
        liability_accounts=liability_items,
        equity_accounts=equity_items
    )

def extract_company_name(raw_text: str) -> str:
    """Extract company name from raw text."""
    # Look for NVIDIA CORPORATION pattern
    match = re.search(r'(NVIDIA CORPORATION[^\n]*)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Unknown Company"

def extract_document_title(raw_text: str) -> str:
    """Extract document title from raw text."""
    # Look for CONSOLIDATED BALANCE SHEETS pattern
    match = re.search(r'(CONSOLIDATED BALANCE SHEETS[^\n]*)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Balance Sheet"

def extract_units_note(raw_text: str) -> str:
    """Extract units note from raw text."""
    # Look for (In millions, except par value) pattern
    match = re.search(r'\(([^)]*millions[^)]*)\)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "In millions"

def extract_reporting_periods(raw_text: str) -> List[str]:
    """Extract reporting periods from table headers."""
    periods = []
    
    # Look for "January XX, XXXX" patterns in the table header
    matches = re.findall(r'January \d{1,2}, \d{4}', raw_text)
    for match in matches:
        if match not in periods:
            periods.append(match)
    
    # Sort by year (most recent first)
    periods.sort(key=lambda x: int(re.search(r'(\d{4})', x).group(1)), reverse=True)
    
    return periods

def parse_table_data(raw_text: str, reporting_periods: List[str]) -> List[BalanceSheetAccount]:
    """Parse the actual table data from pipe-separated format."""
    line_items = []
    
    # Find all table rows between the |...| patterns - balance sheet has 3 columns
    table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|', raw_text)
    
    logger.debug_detailed(f"Found {len(table_rows)} potential data rows to parse")
    
    # Track current section context for proper indentation
    current_section = None
    
    for i, row in enumerate(table_rows):
        # Clean up the row data
        account_name = row[0].strip()
        val1 = clean_value(row[1])  # Most recent period  
        val2 = clean_value(row[2])  # Prior period
        
        # Skip header rows, empty rows, and metadata lines
        if not account_name or account_name.lower() in ['january 26, 2020', 'january 27, 2019', ''] or account_name.startswith('#'):
            continue
            
        # Skip separator rows and very long lines (table formatting)
        if '---' in account_name or '+' in account_name or len(account_name) > 100:
            continue
        
        logger.debug_detailed(f"Parsing: {account_name[:50]}...")
        
        # Check if this is a section header (no values in val1 and val2)
        has_values = bool(val1 or val2)
        is_section_header = is_section_header_account(account_name) or not has_values
        
        if is_section_header and not has_values:
            current_section = account_name
            logger.debug_detailed(f"  ✅ Section header detected - setting context to '{current_section}'")
            # Add section header as a line item but with empty values
            line_item = BalanceSheetAccount(
                account_name=account_name,
                values={},  # Section headers have no values
                account_category="section_header",
                is_section_header=True,
                indent_level=0,  # Section headers are at main level
                parent_section="",
                account_subcategory="",
                is_total=False
            )
            line_items.append(line_item)
            logger.debug_detailed(f"  ✅ Section header added to output")
            continue
        
        # Determine account category and indentation with context
        account_category = categorize_account(account_name)
        indent_level = determine_indent_level_with_context(account_name, current_section)
        parent_section = get_parent_section_with_context(account_name, current_section)
        
        # Create values dictionary
        values = {}
        if len(reporting_periods) >= 2:
            if val1:  # Most recent year
                values[reporting_periods[0]] = val1
            if val2:  # Prior year  
                values[reporting_periods[1]] = val2
        
        # Reset context after total lines
        if is_total_line_that_resets_context(account_name):
            current_section = None
        
        if values:  # Only add if we have actual values
            line_item = BalanceSheetAccount(
                account_name=account_name,
                values=values,
                account_category=account_category,
                is_section_header=False,
                indent_level=indent_level,
                parent_section=parent_section,
                account_subcategory=get_subcategory(account_name),
                is_total=is_calculated_field(account_name)
            )
            line_items.append(line_item)
            logger.debug_detailed(f"  ✅ Mapped {len(values)} periods (indent: {indent_level}, parent: {parent_section})")
        else:
            logger.debug_detailed(f"  ⚠️ No values found, skipping")
    
    return line_items

def clean_value(value: str) -> str:
    """Clean and standardize monetary values."""
    if not value or not value.strip():
        return ""
    
    # Remove extra whitespace
    value = value.strip()
    
    # Skip empty values or dashes
    if value in ['-', '—', '']:
        return ""
    
    # Keep the value as-is (including $ signs and parentheses)
    return value

def categorize_account(account_name: str) -> str:
    """Categorize account into asset, liability, or equity."""
    name_lower = account_name.lower()
    
    # Asset items - look for asset keywords or position in document
    if any(keyword in name_lower for keyword in [
        'asset', 'cash', 'marketable securities', 'accounts receivable', 
        'inventories', 'prepaid', 'property', 'equipment', 'goodwill', 
        'intangible', 'deferred', 'operating lease assets'
    ]):
        return "asset"
    
    # Liability items
    if any(keyword in name_lower for keyword in [
        'liabilit', 'payable', 'accrued', 'debt', 'deferred revenue',
        'operating lease liabilit', 'income tax', 'other liabilit'
    ]):
        return "liability"
    
    # Equity items  
    if any(keyword in name_lower for keyword in [
        'equity', 'stockholders', 'shareholders', 'common stock', 
        'retained earnings', 'accumulated', 'additional paid-in', 
        'treasury stock', 'capital'
    ]):
        return "equity"
    
    # Default categorization based on typical balance sheet structure
    if 'total' in name_lower:
        if any(word in name_lower for word in ['asset']):
            return "asset"
        elif any(word in name_lower for word in ['liability', 'liabilities']):
            return "liability"
        elif any(word in name_lower for word in ['equity', 'stockholders']):
            return "equity"
    
    # Default to asset (since assets typically come first)
    return "asset"

def determine_indent_level(account_name: str) -> int:
    """Determine indentation level based on context."""
    name_lower = account_name.lower()
    
    # Sub-items (indented)
    if any(keyword in name_lower for keyword in [
        'cash and cash equivalents', 'marketable securities', 'accounts receivable',
        'inventories', 'prepaid expenses', 'property and equipment',
        'accounts payable', 'accrued compensation', 'deferred revenue'
    ]):
        return 1
    
    # Section headers and totals
    if any(keyword in name_lower for keyword in [
        'current assets', 'current liabilities', 'stockholders'
    ]) or 'total' in name_lower:
        return 0
        
    # Main categories
    if name_lower in ['assets', 'liabilities and stockholders\' equity']:
        return 0
    
    # Default to level 1 for line items
    return 1

def determine_indent_level_with_context(account_name: str, current_section: str) -> int:
    """Determine indentation level using current section context."""
    name_lower = account_name.lower()
    
    # Main section headers
    if any(keyword in name_lower for keyword in [
        'assets', 'liabilities and stockholders\' equity', 'shareholders\' equity'
    ]):
        return 0
    
    # Subsection headers  
    if any(keyword in name_lower for keyword in [
        'current assets', 'current liabilities', 'stockholders\' equity'
    ]):
        return 0
    
    # Total lines
    if 'total' in name_lower:
        return 0 if 'total assets' in name_lower or 'total liabilities' in name_lower else 0
        
    # Line items under current section context
    if current_section:
        return 1
    
    # Default level for line items
    return 1

def get_parent_section_with_context(account_name: str, current_section: str) -> str:
    """Get parent section using current context."""
    if current_section:
        return current_section
    return get_parent_section(account_name)

def is_total_line_that_resets_context(account_name: str) -> bool:
    """Check if this total line should reset the section context."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        'total current assets', 'total assets', 'total current liabilities', 
        'total liabilities', 'total stockholders\' equity', 'total shareholders\' equity',
        'total liabilities and stockholders\' equity'
    ])

def is_section_header_account(account_name: str) -> bool:
    """Check if account is a section header (no numerical values)."""
    name_lower = account_name.lower()
    
    # Main section headers
    if any(keyword in name_lower for keyword in [
        'assets', 'liabilities and shareholders\' equity', 'shareholders\' equity', 
        'current assets:', 'current liabilities:', 'stockholders\' equity:'
    ]) and 'total' not in name_lower:
        return True
    
    # Check if line has no numbers/dollars (likely a section header)
    if not re.search(r'\$|\d', account_name):
        # But exclude obvious non-headers
        if any(skip in name_lower for skip in ['table of contents', 'see accompanying', 'note']):
            return False
        return True
    
    return False

def get_parent_section(account_name: str) -> str:
    """Get parent section for categorization."""
    name_lower = account_name.lower()
    
    # Current assets items
    if any(keyword in name_lower for keyword in [
        'cash and cash equivalents', 'marketable securities', 'accounts receivable',
        'inventories', 'prepaid expenses'
    ]):
        return "Current assets"
    
    # Current liabilities items  
    if any(keyword in name_lower for keyword in [
        'accounts payable', 'accrued compensation', 'deferred revenue'
    ]):
        return "Current liabilities"
        
    # Stockholders' equity items
    if any(keyword in name_lower for keyword in [
        'common stock', 'retained earnings', 'accumulated other'
    ]):
        return "Stockholders' equity"
    
    return ""

def is_calculated_field(account_name: str) -> bool:
    """Check if field is calculated (totals, etc.)."""
    name_lower = account_name.lower()
    return 'total' in name_lower

def get_subcategory(account_name: str) -> str:
    """Get account subcategory."""
    name_lower = account_name.lower()
    
    if 'current' in name_lower:
        return "current"
    elif any(keyword in name_lower for keyword in ['long-term', 'non-current']):
        return "non-current"
    
    return ""

if __name__ == "__main__":
    # Test the parser
    result = parse_balance_sheet_directly("output/balance sheet_raw.txt")
    logger.debug(f"\n🎉 Parsing complete!")
    logger.debug(f"Company: {result.company_name}")
    logger.debug(f"Periods: {result.reporting_periods}")
    logger.debug(f"Line items: {len(result.line_items)}")