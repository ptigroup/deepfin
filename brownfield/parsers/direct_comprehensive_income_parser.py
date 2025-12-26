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
from core.pipeline_logger import logger

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
    
    # Find all table rows - comprehensive income uses different format patterns
    # Try pipe-separated format first
    table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]*)\|', raw_text)
    
    if not table_rows:
        # Try the +---+ bordered format (as seen in the raw text)
        # Look for rows with account names and values
        lines = raw_text.split('\n')
        table_rows = []
        
        for line in lines:
            # Skip separator lines
            if '+---' in line or line.strip() == '':
                continue
            
            # Look for data lines with | separators
            if '|' in line and any(char.isdigit() or char in '$()' for char in line):
                # Split by | and clean up
                parts = [part.strip() for part in line.split('|')]
                if len(parts) >= 4:  # Account name + at least 3 values
                    account_name = parts[0].strip()
                    values = [part.strip() for part in parts[1:] if part.strip()]
                    if account_name:  # Only add if we have an account name
                        # Pad with empty values to match expected format
                        while len(values) < 5:
                            values.append('')
                        table_rows.append([account_name] + values[:5])
    
    column_count = 6  # Account name + 5 value columns
    
    logger.debug_detailed(f"Found {len(table_rows)} potential data rows to parse")
    
    # Track current section context for proper parent assignment
    current_section = ""
    
    for row in table_rows:
        # Clean up the row data based on column count
        account_name = row[0].strip()
        values_raw = [clean_value(row[i]) for i in range(1, min(len(row), 6))]  # Up to 5 value columns
        
        # Filter out empty values from the end
        while values_raw and not values_raw[-1]:
            values_raw.pop()
        
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
        
        # Track section context and determine parent section
        if is_section_header_account(account_name):
            if 'available-for-sale' in account_name.lower():
                current_section = "Available-for-sale debt securities"
            elif 'cash flow hedges' in account_name.lower():
                current_section = "Cash flow hedges"
            else:
                current_section = ""
            parent_section = ""
        else:
            # Use context-based parent section assignment for sub-items
            if any(keyword in account_name.lower() for keyword in ['net unrealized', 'reclassification', 'net change']):
                parent_section = current_section
            else:
                parent_section = ""
        
        # Create values dictionary - map values to periods
        values = {}
        for i, val in enumerate(values_raw):
            if i < len(reporting_periods) and val:
                values[reporting_periods[i]] = val
        
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
    
    # Only process sub-items under main OCI categories
    if not any(keyword in name_lower for keyword in [
        'net unrealized', 'reclassification', 'net change'
    ]):
        return ""
    
    # Find the position of this account name in the raw text
    account_pos = raw_text.find(account_name)
    if account_pos == -1:
        return ""
    
    # Look backwards in the text to find the most recent section header
    preceding_text = raw_text[:account_pos].lower()
    
    # Check for Cash flow hedges section - look for the most recent occurrence
    # Search for variations of the section headers, including table formatting
    cash_flow_searches = [
        'cash flow hedges',
        'cash flow hedges:',
        '| cash flow hedges',
        '| cash flow hedges:'
    ]
    
    available_for_sale_searches = [
        'available-for-sale',
        'available-for-sale debt securities',
        '| available-for-sale',
        '| available-for-sale debt securities'
    ]
    
    cash_flow_pos = max([preceding_text.rfind(search) for search in cash_flow_searches])
    available_for_sale_pos = max([preceding_text.rfind(search) for search in available_for_sale_searches])
    
    
    # Determine which section header is more recent (closer to our account)
    if cash_flow_pos > available_for_sale_pos and cash_flow_pos != -1:
        return "Cash flow hedges"
    elif available_for_sale_pos != -1:
        return "Available-for-sale debt securities"
    
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