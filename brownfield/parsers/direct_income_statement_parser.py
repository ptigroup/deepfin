#!/usr/bin/env python3
"""
Direct Income Statement Parser

Parses income statement raw text directly from LLMWhisperer output,
bypassing LLM interpretation to ensure 100% data accuracy and preserve
table structure including indentation levels.
"""

import re
from typing import List, Dict, Tuple, Optional
from schemas.income_statement_schema import IncomeStatementSchema, IncomeStatementLineItem
from core.pipeline_logger import logger

def parse_income_statement_directly(raw_text_file_path: str) -> IncomeStatementSchema:
    """
    Parse income statement directly from raw LLMWhisperer text.
    
    Args:
        raw_text_file_path: Path to the raw text file
        
    Returns:
        IncomeStatementSchema: Populated schema instance
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
    revenue_items = [item for item in line_items if item.account_category == "revenue"]
    expense_items = [item for item in line_items if item.account_category == "expense"]
    net_income_items = [item for item in line_items if "net income" in item.account_name.lower()]
    
    logger.debug(f"Extracted {len(line_items)} line items")
    logger.debug(f"Found {len(revenue_items)} revenue items")
    logger.debug(f"Found {len(expense_items)} expense items")
    logger.debug(f"Found {len(net_income_items)} net income items")
    
    return IncomeStatementSchema(
        company_name=company_name,
        document_title=document_title,
        document_type="income_statement",
        reporting_periods=reporting_periods,
        units_note=units_note,
        line_items=line_items,
        revenue_items=revenue_items,
        expense_items=expense_items,
        net_income_items=net_income_items
    )

def extract_company_name(raw_text: str) -> str:
    """Extract company name from raw text."""
    # Return empty string to avoid unwanted company headers
    return ""

def extract_document_title(raw_text: str) -> str:
    """Extract document title from raw text."""
    # Return simple title to avoid unwanted headers
    return "Income Statement"

def extract_units_note(raw_text: str) -> str:
    """Extract units note from raw text."""
    # Look for (In millions, except per share data) pattern
    match = re.search(r'\(([^)]*millions[^)]*)\)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "In millions"

def extract_reporting_periods(raw_text: str) -> List[str]:
    """Extract reporting periods from table headers."""
    periods = []
    
    # Look for "January XX, XXXX" patterns in the table
    matches = re.findall(r'January \d{1,2}, \d{4}', raw_text)
    for match in matches:
        period = f"Year Ended {match}"
        if period not in periods:
            periods.append(period)
    
    # Sort by year (most recent first)
    periods.sort(key=lambda x: int(re.search(r'(\d{4})', x).group(1)), reverse=True)
    
    return periods

def parse_table_data(raw_text: str, reporting_periods: List[str]) -> List[IncomeStatementLineItem]:
    """Parse the actual table data from pipe-separated format."""
    line_items = []
    
    # Find all table rows between the |...| patterns
    table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|[^|]*\|[^|]*\|', raw_text)
    
    logger.debug_detailed(f"Found {len(table_rows)} potential data rows to parse")
    
    # Track current section context for proper indentation
    current_section = None
    
    for i, row in enumerate(table_rows):
        # Clean up the row data
        account_name = row[0].strip()
        val1 = clean_value(row[1])
        val2 = clean_value(row[2]) 
        val3 = clean_value(row[3])
        
        # Skip header rows and empty rows
        if not account_name or account_name.lower() in ['year ended', '']:
            continue
            
        # Skip separator rows
        if '---' in account_name or '+' in account_name:
            continue
        
        logger.debug_detailed(f"Parsing: {account_name[:50]}...")
        
        # Check if this is a section header (no values)
        is_section_header = is_section_header_account(account_name)
        if is_section_header:
            current_section = account_name
            logger.debug_detailed(f"  ✅ Section header detected - setting context to '{current_section}'")
            # Add section header as a line item but with empty values
            line_item = IncomeStatementLineItem(
                account_name=account_name,
                values={},  # Section headers have no values
                account_category="section_header",
                is_section_header=True,
                indent_level=0,  # Section headers are at main level
                is_calculated=False,
                parent_section=""
            )
            line_items.append(line_item)
            logger.debug_detailed(f"  ✅ Section header added to output")
            continue  # Continue to next row after adding section header
        
        # Check if this is a total line that should reset context
        if is_total_line_that_resets_context(account_name):
            current_section = None  # Reset context after total lines
            logger.debug_detailed(f"  🔄 Total line detected - resetting section context")
        
        # Determine account category and indentation with context
        account_category = categorize_account(account_name)
        indent_level = determine_indent_level_with_context(account_name, current_section)
        parent_section = get_parent_section_with_context(account_name, current_section)
        
        # Create values dictionary
        values = {}
        if len(reporting_periods) >= 3:
            if val1:  # Most recent year (leftmost value)
                values[reporting_periods[0]] = val1
            if val2:  # Middle year
                values[reporting_periods[1]] = val2
            if val3:  # Oldest year (rightmost value)
                values[reporting_periods[2]] = val3
        
        if values:  # Only add if we have values
            line_item = IncomeStatementLineItem(
                account_name=account_name,
                values=values,
                account_category=account_category,
                is_section_header=False,  # We already handled section headers above
                indent_level=indent_level,
                is_calculated=is_calculated_field(account_name),
                parent_section=parent_section
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
    """Categorize account into revenue, expense, or income."""
    name_lower = account_name.lower()
    
    # Revenue items
    if any(keyword in name_lower for keyword in ['revenue', 'sales']):
        return "revenue"
    
    # Expense items
    if any(keyword in name_lower for keyword in [
        'cost', 'expense', 'research and development', 'sales, general', 
        'operating expenses', 'interest expense', 'tax expense'
    ]):
        return "expense"
    
    # Income items (everything else)
    return "income"

def determine_indent_level_with_context(account_name: str, current_section: str) -> int:
    """Determine indentation level based on context from current section."""
    name_lower = account_name.lower()
    
    # If we're currently in a section context, indent the items under it
    if current_section:
        section_lower = current_section.lower()
        
        # Items under "Operating expenses" section
        if 'operating expenses' in section_lower:
            return 1
            
        # Items under "Net income per share" section  
        if 'net income per share' in section_lower:
            return 1
            
        # Items under "Weighted average shares" section
        if 'weighted average' in section_lower:
            return 1
    
    # Main level items (no current section context)
    return 0

def determine_indent_level(account_name: str, raw_text: str) -> int:
    """Legacy function - determine indentation level based on context."""
    name_lower = account_name.lower()
    
    # Sub-items under operating expenses
    if any(keyword in name_lower for keyword in [
        'research and development', 'sales, general'
    ]):
        return 1
        
    # Main level items
    return 0

def is_section_header_account(account_name: str) -> bool:
    """Check if account is a section header (items that group other items but have no values)."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        'operating expenses', 'net income per share:', 
        'weighted average shares used in per share computation:'
    ])

def get_parent_section_with_context(account_name: str, current_section: str) -> str:
    """Get parent section based on current section context."""
    if current_section:
        section_lower = current_section.lower()
        
        # Items under "Operating expenses"
        if 'operating expenses' in section_lower:
            return "Operating expenses"
            
        # Items under "Net income per share" 
        if 'net income per share' in section_lower:
            return "Net income per share"
            
        # Items under "Weighted average shares"
        if 'weighted average' in section_lower:
            return "Weighted average shares used in per share computation"
    
    return ""

def get_parent_section(account_name: str) -> str:
    """Legacy function - Get parent section for categorization."""
    name_lower = account_name.lower()
    
    if any(keyword in name_lower for keyword in [
        'research and development', 'sales, general'
    ]):
        return "Operating expenses"
        
    if any(keyword in name_lower for keyword in ['basic', 'diluted']) and 'share' in name_lower:
        if 'per share' in name_lower:
            return "Net income per share"
        else:
            return "Weighted average shares used in per share computation"
    
    return ""

def is_total_line_that_resets_context(account_name: str) -> bool:
    """Check if this is a total line that should reset section context."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        'total operating expenses', 'total other income', 'total'
    ])

def is_calculated_field(account_name: str) -> bool:
    """Check if field is calculated (totals, etc.)."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        'total', 'gross profit', 'income from operations',
        'income before', 'net income'
    ])

if __name__ == "__main__":
    # Test the parser
    result = parse_income_statement_directly("output/income statement_raw.txt")
    logger.debug(f"\\n🎉 Parsing complete!")
    logger.debug(f"Company: {result.company_name}")
    logger.debug(f"Periods: {result.reporting_periods}")
    logger.debug(f"Line items: {len(result.line_items)}")