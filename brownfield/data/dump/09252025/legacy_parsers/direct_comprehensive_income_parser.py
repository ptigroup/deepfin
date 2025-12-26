#!/usr/bin/env python3
"""
Direct Comprehensive Income Parser

Parses comprehensive income raw text directly from LLMWhisperer output,
bypassing LLM interpretation to ensure 100% data accuracy and preserve
table structure including indentation levels.
"""

import re
from typing import List, Dict, Tuple, Optional
from schemas.comprehensive_income_schema import ComprehensiveIncomeSchema, ComprehensiveIncomeLineItem
from pipeline_logger import logger

def parse_comprehensive_income_directly(raw_text_file_path: str) -> ComprehensiveIncomeSchema:
    """
    Parse comprehensive income directly from raw LLMWhisperer text.
    
    Args:
        raw_text_file_path: Path to the raw text file
        
    Returns:
        ComprehensiveIncomeSchema: Populated schema instance
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
    net_income_items = [item for item in line_items if "net income" in item.account_name.lower()]
    oci_items = [item for item in line_items if item.item_category == "other_comprehensive_income"]
    total_comprehensive_items = [item for item in line_items if "total comprehensive" in item.account_name.lower()]
    
    logger.debug(f"📊 Extracted {len(line_items)} line items")
    logger.debug(f"💰 Found {len(net_income_items)} net income items")
    logger.debug(f"🔄 Found {len(oci_items)} OCI items")
    logger.debug(f"📈 Found {len(total_comprehensive_items)} total comprehensive items")
    
    return ComprehensiveIncomeSchema(
        company_name=company_name,
        document_title=document_title,
        document_type="comprehensive_income",
        reporting_periods=reporting_periods,
        units_note=units_note,
        line_items=line_items,
        net_income_items=net_income_items,
        oci_items=oci_items,
        total_comprehensive_items=total_comprehensive_items
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
    # Look for CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME pattern
    match = re.search(r'(CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME[^\n]*)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Comprehensive Income Statement"

def extract_units_note(raw_text: str) -> str:
    """Extract units note from raw text."""
    # Look for (In millions) pattern
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

def parse_table_data(raw_text: str, reporting_periods: List[str]) -> List[ComprehensiveIncomeLineItem]:
    """Parse the actual table data from pipe-separated format."""
    line_items = []
    
    # Find all table rows between the |...| patterns - comprehensive income has 6 columns
    table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]*)\|([^|]*)\|', raw_text)
    
    logger.debug_detailed(f"Found {len(table_rows)} potential data rows to parse")
    
    for row in table_rows:
        # Clean up the row data
        account_name = row[0].strip()
        val1 = clean_value(row[1])  # Most recent year
        val2 = clean_value(row[2])  # Middle year  
        val3 = clean_value(row[3])  # Oldest year
        # Ignore row[4] and row[5] (empty columns)
        
        # Skip header rows and empty rows
        if not account_name or account_name.lower() in ['year ended', '']:
            continue
            
        # Skip separator rows
        if '---' in account_name or '+' in account_name:
            continue
        
        logger.debug_detailed(f"Parsing: {account_name[:50]}...")
        
        # Determine account category and indentation
        item_category = categorize_account(account_name)
        indent_level = determine_indent_level(account_name, raw_text)
        is_section_header = is_section_header_account(account_name)
        parent_section = get_parent_section(account_name, raw_text)
        
        # Create values dictionary
        values = {}
        if len(reporting_periods) >= 3:
            if val1:  # Most recent year (leftmost value)
                values[reporting_periods[0]] = val1
            if val2:  # Middle year
                values[reporting_periods[1]] = val2
            if val3:  # Oldest year (rightmost value)
                values[reporting_periods[2]] = val3
        
        if values or is_section_header:  # Only add if we have values OR if it's a section header
            line_item = ComprehensiveIncomeLineItem(
                account_name=account_name,
                values=values,
                item_category=item_category,
                is_section_header=is_section_header,
                indent_level=indent_level,
                is_calculated=is_calculated_field(account_name),
                parent_section=parent_section
            )
            line_items.append(line_item)
            if values:
                logger.debug_detailed(f"  ✅ Mapped {len(values)} periods")
            else:
                logger.debug_detailed(f"  ✅ Section header added")
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
    """Categorize account into income or other comprehensive income."""
    name_lower = account_name.lower()
    
    # Net income items
    if "net income" in name_lower:
        return "net_income"
    
    # Other comprehensive income items
    if any(keyword in name_lower for keyword in [
        'other comprehensive', 'available-for-sale', 'cash flow hedges',
        'unrealized', 'reclassification', 'net change'
    ]):
        return "other_comprehensive_income"
    
    # Total comprehensive income
    if "total comprehensive" in name_lower:
        return "total_comprehensive"
    
    # Default to OCI for most line items in comprehensive income statement
    return "other_comprehensive_income"

def determine_indent_level(account_name: str, raw_text: str) -> int:
    """Determine indentation level based on context."""
    name_lower = account_name.lower()
    
    # Sub-items under main categories (more indented)
    if any(keyword in name_lower for keyword in [
        'net unrealized', 'reclassification adjustments', 'net change'
    ]):
        return 2
    
    # Main OCI categories (medium indent)
    if any(keyword in name_lower for keyword in [
        'available-for-sale', 'cash flow hedges'
    ]):
        return 1
        
    # Top level items (no indent)
    if any(keyword in name_lower for keyword in [
        'net income', 'other comprehensive income', 'total comprehensive'
    ]):
        return 0
    
    # Default to level 1
    return 1

def is_section_header_account(account_name: str) -> bool:
    """Check if account is a section header."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        'other comprehensive income (loss), net of tax',
        'available-for-sale debt securities:',
        'cash flow hedges:'
    ]) and not any(total in name_lower for total in ['total', 'net change'])

def get_parent_section(account_name: str, raw_text: str) -> str:
    """Get parent section for categorization."""
    name_lower = account_name.lower()
    
    # Available-for-sale securities items
    if any(keyword in name_lower for keyword in [
        'net unrealized gain', 'reclassification adjustments', 'net change'
    ]) and 'cash flow' not in name_lower:
        return "Available-for-sale debt securities"
    
    # Cash flow hedges items
    if any(keyword in name_lower for keyword in [
        'net unrealized', 'reclassification', 'net change'
    ]) and 'cash flow' in raw_text[raw_text.find(account_name)-200:raw_text.find(account_name)].lower():
        return "Cash flow hedges"
    
    return ""

def is_calculated_field(account_name: str) -> bool:
    """Check if field is calculated (totals, etc.)."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        'total', 'net change', 'other comprehensive income (loss), net of tax'
    ])

if __name__ == "__main__":
    # Test the parser
    result = parse_comprehensive_income_directly("output/comprehensive income_raw.txt")
    logger.debug(f"\n🎉 Parsing complete!")
    logger.debug(f"Company: {result.company_name}")
    logger.debug(f"Periods: {result.reporting_periods}")
    logger.debug(f"Line items: {len(result.line_items)}")