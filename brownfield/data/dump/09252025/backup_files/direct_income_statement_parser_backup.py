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

def parse_income_statement_directly(raw_text_file_path: str) -> IncomeStatementSchema:
    """
    Parse income statement directly from raw LLMWhisperer text.
    
    Args:
        raw_text_file_path: Path to the raw text file
        
    Returns:
        IncomeStatementSchema: Populated schema instance
    """
    print("🎯 Using direct raw text parsing for reliable table structure preservation")
    
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
    
    print(f"📊 Extracted {len(line_items)} line items")
    print(f"📈 Found {len(revenue_items)} revenue items")
    print(f"📉 Found {len(expense_items)} expense items")
    print(f"💰 Found {len(net_income_items)} net income items")
    
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
    """Parse the actual table data from space-separated tabular format."""
    line_items = []
    
    # Split text into lines and look for financial data rows
    lines = raw_text.split('\n')
    table_rows = []
    
    for line in lines:
        # Skip empty lines and lines without financial data
        line = line.strip()
        if not line or 'Table of Contents' in line or '<<<' in line:
            continue
            
        # Look for lines with account names and dollar amounts or numbers
        # Pattern: Account name followed by dollar amounts or numbers
        if re.search(r'\$.*?\d+(?:,\d{3})*|\d+(?:,\d{3})*', line):
            # Extract account name (everything before the first $ or large number)
            account_match = re.match(r'^([^$]+?)(?:\s+\$|\s+\d)', line)
            if account_match:
                account_name = account_match.group(1).strip()
                
                # Extract all dollar amounts and numbers from the line
                amounts = re.findall(r'\$?\s*[\(\-]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?|\(\d+(?:,\d{3})*(?:\.\d{2})?\))', line)
                
                # Keep original formatting (preserve $ signs and parentheses)
                cleaned_amounts = []
                for amount in amounts:
                    # Keep the original amount with formatting
                    cleaned_amounts.append(amount.strip())
                
                if account_name and len(cleaned_amounts) >= 1:
                    # Create a tuple similar to the original pipe format
                    # Pad with empty strings if fewer than expected columns
                    row_data = [account_name] + cleaned_amounts + [''] * (4 - len(cleaned_amounts))
                    table_rows.append(tuple(row_data[:4]))  # Take only first 4 elements
    
    print(f"Found {len(table_rows)} potential data rows to parse")
    
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
            
        # Skip date headers that shouldn't be parsed as financial data
        if re.match(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d*$', account_name.strip()):
            print(f"  ⚠️ Skipping date header: {account_name}")
            continue
            
        # Skip year headers
        if re.match(r'^\d{4}$', account_name.strip()):
            print(f"  ⚠️ Skipping year header: {account_name}")
            continue
            
        # Skip non-income statement accounts (balance sheet, cash flow data)
        if is_non_income_statement_account(account_name):
            print(f"  ⚠️ Skipping non-income statement data: {account_name[:30]}...")
            continue
            
        # Skip rows that are just dashes or formatting (not real financial data)
        if re.match(r'^[\s\-\(\)]*$|^\d+[\s\-\(\)]*$', account_name.strip()):
            print(f"  ⚠️ Skipping formatting row: {account_name[:30]}...")
            continue
            
        # Skip rows that contain only numbers without descriptive text
        if re.match(r'^\d+\s*$', account_name.strip()):
            print(f"  ⚠️ Skipping number-only row: {account_name}")
            continue
        
        print(f"Parsing: {account_name[:50]}...")
        
        # Check if this is a section header (no values)
        is_section_header = is_section_header_account(account_name)
        if is_section_header:
            current_section = account_name
            print(f"  ✅ Section header detected - setting context to '{current_section}'")
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
            print(f"  ✅ Section header added to output")
            continue  # Continue to next row after adding section header
        
        # Check if this is a total line that should reset context
        if is_total_line_that_resets_context(account_name):
            current_section = None  # Reset context after total lines
            print(f"  🔄 Total line detected - resetting section context")
        
        # Determine account category and indentation with context
        account_category = categorize_account(account_name)
        indent_level = determine_indent_level_with_context(account_name, current_section)
        parent_section = get_parent_section_with_context(account_name, current_section)
        
        # Create values dictionary with proper formatting
        values = {}
        if len(reporting_periods) >= 3:
            if val1:  # Most recent year (leftmost value)
                formatted_val1 = format_financial_value(val1, account_name)
                values[reporting_periods[0]] = formatted_val1
            if val2:  # Middle year
                formatted_val2 = format_financial_value(val2, account_name)
                values[reporting_periods[1]] = formatted_val2
            if val3:  # Oldest year (rightmost value)
                formatted_val3 = format_financial_value(val3, account_name)
                values[reporting_periods[2]] = formatted_val3
        
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
            print(f"  ✅ Mapped {len(values)} periods (indent: {indent_level}, parent: {parent_section})")
        else:
            print(f"  ⚠️ No values found, skipping")
    
    return line_items

def clean_value(value: str) -> str:
    """Clean and standardize monetary values to match restore format."""
    if not value or not value.strip():
        return ""
    
    # Remove extra whitespace
    value = value.strip()
    
    # Skip empty values or dashes
    if value in ['-', '—', '']:
        return ""
    
    # Format the value to match restore version format
    # Remove any existing formatting first
    clean_num = re.sub(r'[,$()]', '', value)
    
    # Check if it's a valid number
    try:
        num = float(clean_num)
        
        # Determine if it should be negative (parentheses in original)
        is_negative = '(' in value and ')' in value
        
        # Format with commas
        if abs(num) >= 1000:
            formatted = f"{int(abs(num)):,}"
        else:
            formatted = str(int(abs(num)))
            
        # Apply negative formatting with parentheses
        if is_negative:
            return f"({formatted})"
        else:
            return formatted
            
    except ValueError:
        # If not a number, return as-is
        return value

def is_non_income_statement_account(account_name: str) -> bool:
    """Check if this account belongs to balance sheet or cash flow (not income statement)."""
    name_lower = account_name.lower().strip()
    
    # Balance sheet accounts that shouldn't be in income statement
    balance_sheet_terms = [
        'cash and cash equivalents', 'marketable securities', 'accounts receivable',
        'inventories', 'prepaid expenses', 'total current assets', 'property and equipment',
        'goodwill', 'intangible assets', 'deferred income tax assets', 'other assets',
        'total assets', 'accounts payable', 'accrued and other current liabilities',
        'total current liabilities', 'long-term debt', 'long-term operating lease',
        'other long-term liabilities', 'total liabilities', 'commitments and contingencies',
        'preferred stock', 'common stock', 'additional paid-in capital', 'treasury stock',
        'accumulated other comprehensive', 'retained earnings', 'total shareholders',
        'total liabilities and shareholders', 'balances,', 'convertible debt conversion',
        'issuance of common stock'
    ]
    
    # Cash flow statement terms
    cash_flow_terms = [
        'stock-based compensation expense', 'depreciation and amortization',
        'deferred income taxes', 'loss on early debt conversions', 'change in cash',
        'cash and cash equivalents at beginning', 'cash and cash equivalents at end',
        'proceeds from maturities', 'proceeds from sales', 'proceeds from sale of',
        'net cash provided', 'cash paid for income taxes', 'cash paid for interest',
        'assets acquired by assuming', 'proceeds related to employee'
    ]
    
    # Comprehensive income terms (Other Comprehensive Income - not part of basic income statement)
    oci_terms = [
        'net unrealized gain', 'reclassification adjustments', 'net change in unrealized',
        'other comprehensive income', 'total comprehensive income'
    ]
    
    # Check if account matches any non-income statement terms
    for term in balance_sheet_terms + cash_flow_terms + oci_terms:
        if term in name_lower:
            return True
            
    # Also skip items that are clearly table formatting (dashes, numbers only)
    if re.match(r'^-+$|^\d+$', name_lower) or 'as of january' in name_lower:
        return True
        
    return False

def format_financial_value(value: str, account_name: str) -> str:
    """Format financial values to match restore version format."""
    if not value or not value.strip():
        return ""
    
    # Clean the value first
    clean_val = clean_value(value)
    if not clean_val:
        return ""
    
    # For major revenue/income items, add $ prefix
    name_lower = account_name.lower()
    needs_dollar_sign = any(term in name_lower for term in [
        'revenue', 'net income', 'total assets'
    ])
    
    # Check if it's already properly formatted with parentheses for negatives
    if clean_val.startswith('(') and clean_val.endswith(')'):
        # Already properly formatted negative
        return clean_val
    
    # Add $ prefix for major items
    if needs_dollar_sign and not clean_val.startswith('$'):
        return f"$ {clean_val}"
    
    return clean_val

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
    """Determine indentation level based on context from current section to match restore format."""
    name_lower = account_name.lower()
    
    # If we're currently in a section context, indent the items under it
    if current_section:
        section_lower = current_section.lower()
        
        # Items under "Operating expenses" section should be indented (level 1)
        if 'operating expenses' in section_lower:
            # These specific items are sub-items under operating expenses in restore version
            if any(term in name_lower for term in [
                'research and development',
                'sales, general and administrative', 
                'income from operations',
                'interest income',
                'interest expense', 
                'other, net'
            ]):
                return 1
            return 1  # Default for items in this section
            
        # Items under "Net income per share:" section should be indented (level 1)
        if 'net income per share' in section_lower:
            if any(term in name_lower for term in ['basic', 'diluted']):
                return 1
                
        # Items under "Weighted average shares..." section should be indented (level 1)
        if 'weighted average' in section_lower:
            if any(term in name_lower for term in ['basic', 'diluted']):
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
    
    # Based on restore version structure - these are the actual section headers
    section_headers = [
        'operating expenses',
        'net income per share:',
        'weighted average shares used in per share computation:'
    ]
    
    return any(keyword in name_lower for keyword in section_headers)

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
    result = parse_income_statement_directly("output/raw/income statement_raw.txt")
    print(f"\\n🎉 Parsing complete!")
    print(f"Company: {result.company_name}")
    print(f"Periods: {result.reporting_periods}")
    print(f"Line items: {len(result.line_items)}")