#!/usr/bin/env python3
"""
Direct Cash Flow Parser

Parses cash flow statement raw text directly from LLMWhisperer output,
bypassing LLM interpretation to ensure 100% data accuracy and preserve
table structure including indentation levels and activity categorization.
"""

import re
from typing import List, Dict, Tuple, Optional
from schemas.cash_flow_schema import CashFlowSchema, CashFlowLineItem
from pipeline_logger import logger

def parse_cash_flow_directly(raw_text_file_path: str) -> CashFlowSchema:
    """
    Parse cash flow statement directly from raw LLMWhisperer text.
    
    Args:
        raw_text_file_path: Path to the raw text file
        
    Returns:
        CashFlowSchema: Populated schema instance
    """
    logger.debug("Using direct raw text parsing for cash flow statement")
    
    with open(raw_text_file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Extract company info and metadata
    company_name = extract_company_name(raw_text)
    document_title = extract_document_title(raw_text)
    units_note = extract_units_note(raw_text)
    reporting_periods = extract_reporting_periods(raw_text)
    
    # Parse the table data
    line_items = parse_table_data(raw_text, reporting_periods)
    
    # Categorize line items by activity type
    operating_activities = [item for item in line_items if item.activity_type == "operating"]
    investing_activities = [item for item in line_items if item.activity_type == "investing"]
    financing_activities = [item for item in line_items if item.activity_type == "financing"]
    supplemental_info = [item for item in line_items if item.activity_type == "supplemental"]
    beginning_cash = [item for item in line_items if item.is_reconciliation and "beginning" in item.account_name.lower()]
    ending_cash = [item for item in line_items if item.is_reconciliation and "end" in item.account_name.lower()]
    
    logger.debug(f"Extracted {len(line_items)} line items")
    logger.debug(f"Found {len(operating_activities)} operating activities")
    logger.debug(f"Found {len(investing_activities)} investing activities")
    logger.debug(f"Found {len(financing_activities)} financing activities")
    logger.debug(f"Found {len(supplemental_info)} supplemental items")
    
    return CashFlowSchema(
        company_name=company_name,
        document_title=document_title,
        document_type="cash_flow",
        reporting_periods=reporting_periods,
        units_note=units_note,
        line_items=line_items,
        operating_activities=operating_activities,
        investing_activities=investing_activities,
        financing_activities=financing_activities,
        supplemental_info=supplemental_info,
        beginning_cash=beginning_cash,
        ending_cash=ending_cash
    )

def extract_company_name(raw_text: str) -> str:
    """Extract company name from raw text."""
    # Return empty string to avoid unwanted company headers
    return ""

def extract_document_title(raw_text: str) -> str:
    """Extract document title from raw text."""
    # Return simple title to avoid unwanted headers
    return "Cash Flow Statement"

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

def parse_table_data(raw_text: str, reporting_periods: List[str]) -> List[CashFlowLineItem]:
    """Parse the actual table data from pipe-separated format."""
    line_items = []
    
    # Find all table rows between the |...| patterns
    table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|[^|]*\|[^|]*\|', raw_text)
    
    # Track current activity section context
    current_activity = "operating"  # Default to operating
    
    for row in table_rows:
        account_name = row[0].strip()
        val1 = clean_value(row[1])  # Most recent year
        val2 = clean_value(row[2])  # Middle year  
        val3 = clean_value(row[3])  # Oldest year
        
        # Skip empty rows
        if not account_name or account_name == "":
            continue
        
        # Detect activity section headers
        activity_type = detect_activity_type(account_name)
        if activity_type:
            current_activity = activity_type
            # Include section headers as line items instead of skipping
            line_item = CashFlowLineItem(
                account_name=account_name,
                values={},  # Section headers have no values
                account_category="section_header",
                indent_level=0,
                parent_section="",
                activity_type=current_activity,
                cash_flow_direction="neutral",
                is_subtotal=False,
                is_reconciliation=False,
                is_section_header=True
            )
            line_items.append(line_item)
            continue
        
        # Check for other section headers (like "Adjustments to reconcile...")
        if is_context_section_header(account_name):
            line_item = CashFlowLineItem(
                account_name=account_name,
                values={},  # Section headers have no values
                account_category="section_header",
                indent_level=1,  # Sub-section headers are indented
                parent_section=get_parent_section_with_context(account_name, current_activity),
                activity_type=current_activity,
                cash_flow_direction="neutral",
                is_subtotal=False,
                is_reconciliation=False,
                is_section_header=True
            )
            line_items.append(line_item)
            continue
        
        # Determine if this is a subtotal or reconciliation item
        is_subtotal = is_subtotal_line(account_name)
        is_reconciliation = is_reconciliation_line(account_name)
        
        # Determine cash flow direction
        cash_flow_direction = determine_cash_flow_direction(account_name, val1, val2, val3)
        
        # Determine indentation level
        indent_level = determine_indent_level_with_context(account_name, current_activity)
        parent_section = get_parent_section_with_context(account_name, current_activity)
        
        # Build values dictionary
        values = {}
        if len(reporting_periods) >= 1 and val1:
            values[reporting_periods[0]] = val1
        if len(reporting_periods) >= 2 and val2:
            values[reporting_periods[1]] = val2
        if len(reporting_periods) >= 3 and val3:
            values[reporting_periods[2]] = val3
        
        # Categorize account
        account_category = categorize_cash_flow_account(account_name, current_activity)
        
        # Create line item
        line_item = CashFlowLineItem(
            account_name=account_name,
            values=values,
            account_category=account_category,
            indent_level=indent_level,
            parent_section=parent_section,
            activity_type=current_activity,
            cash_flow_direction=cash_flow_direction,
            is_subtotal=is_subtotal,
            is_reconciliation=is_reconciliation,
            is_section_header=False  # Regular data line items are not headers
        )
        
        line_items.append(line_item)
    
    logger.debug_detailed(f"Parsed {len(table_rows)} table rows into {len(line_items)} line items")
    return line_items

def clean_value(value: str) -> str:
    """Clean and standardize financial values."""
    if not value or value.strip() == "":
        return ""
    
    # Remove extra whitespace
    cleaned = value.strip()
    
    # Handle "—" and "-" as zero or empty
    if cleaned in ["—", "-", "–"]:
        return ""
    
    return cleaned

def detect_activity_type(account_name: str) -> Optional[str]:
    """Detect if this line is an activity section header."""
    name_lower = account_name.lower()
    
    if any(keyword in name_lower for keyword in ["operating activities", "cash flows from operating"]):
        return "operating"
    elif any(keyword in name_lower for keyword in ["investing activities", "cash flows from investing"]):
        return "investing"
    elif any(keyword in name_lower for keyword in ["financing activities", "cash flows from financing"]):
        return "financing"
    elif any(keyword in name_lower for keyword in ["supplemental", "non-cash", "disclosure"]):
        return "supplemental"
    
    return None

def is_subtotal_line(account_name: str) -> bool:
    """Determine if this is a subtotal line."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        "net cash from", "net cash used", "total", "subtotal", "net change"
    ])

def is_reconciliation_line(account_name: str) -> bool:
    """Determine if this is part of cash reconciliation."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        "cash at beginning", "cash at end", "beginning cash", "ending cash",
        "cash and cash equivalents at beginning", "cash and cash equivalents at end"
    ])

def is_context_section_header(account_name: str) -> bool:
    """Detect context section headers that should be included as line items."""
    name_lower = account_name.lower()
    return any(keyword in name_lower for keyword in [
        "adjustments to reconcile", "changes in operating", "changes in assets",
        "supplemental disclosures", "non-cash investing", "non-cash financing",
        "cash paid for", "cash received from", "significant non-cash"
    ])

def determine_cash_flow_direction(account_name: str, val1: str, val2: str, val3: str) -> str:
    """Determine if this represents cash inflow, outflow, or neutral."""
    name_lower = account_name.lower()
    
    # Check account name patterns for common inflows/outflows
    if any(keyword in name_lower for keyword in ["proceeds", "received", "collection", "issuance"]):
        return "inflow"
    elif any(keyword in name_lower for keyword in ["payment", "expenditure", "purchase", "repurchase", "dividend"]):
        return "outflow"
    
    # Check if values are predominantly negative (indicating outflows)
    negative_count = 0
    total_values = 0
    
    for val in [val1, val2, val3]:
        if val and val.strip():
            total_values += 1
            if val.strip().startswith('(') or val.strip().startswith('-'):
                negative_count += 1
    
    if total_values > 0:
        if negative_count / total_values >= 0.5:
            return "outflow"
        else:
            return "inflow"
    
    return "neutral"

def determine_indent_level_with_context(account_name: str, current_activity: str) -> int:
    """Determine indentation level based on account name and context."""
    name_lower = account_name.lower()
    
    # Level 0: Activity section headers and major totals
    if any(keyword in name_lower for keyword in [
        "operating activities", "investing activities", "financing activities",
        "net cash from", "net cash used", "net change in cash", 
        "cash at beginning", "cash at end"
    ]):
        return 0
    
    # Level 1: Main items within activities
    if any(keyword in name_lower for keyword in [
        "net income", "depreciation", "stock-based", "deferred",
        "capital expenditure", "acquisition", "proceeds from",
        "repurchase", "dividend", "borrowing", "repayment"
    ]):
        return 1
    
    # Level 2: Sub-items and adjustments
    if any(keyword in name_lower for keyword in [
        "accounts receivable", "inventory", "accounts payable",
        "accrued", "prepaid", "other assets", "other liabilities"
    ]):
        return 2
    
    # Default: Level 1 for most items
    return 1

def get_parent_section_with_context(account_name: str, current_activity: str) -> str:
    """Get parent section based on current activity context."""
    name_lower = account_name.lower()
    
    # Reconciliation items have no parent section
    if is_reconciliation_line(account_name):
        return ""
    
    # Activity-specific parent sections
    if current_activity == "operating":
        if any(keyword in name_lower for keyword in ["adjustment", "depreciation", "stock-based"]):
            return "Adjustments to reconcile net income"
        elif any(keyword in name_lower for keyword in ["accounts", "inventory", "prepaid", "accrued"]):
            return "Changes in operating assets and liabilities"
        return "Operating Activities"
    
    elif current_activity == "investing":
        return "Investing Activities"
    
    elif current_activity == "financing":
        return "Financing Activities"
    
    elif current_activity == "supplemental":
        return "Supplemental Information"
    
    return ""

def categorize_cash_flow_account(account_name: str, current_activity: str) -> str:
    """Categorize cash flow account based on name and activity."""
    name_lower = account_name.lower()
    
    # Operating activity categories
    if current_activity == "operating":
        if "net income" in name_lower:
            return "net_income"
        elif any(keyword in name_lower for keyword in ["depreciation", "amortization"]):
            return "depreciation_amortization"
        elif "stock-based" in name_lower or "share-based" in name_lower:
            return "stock_compensation"
        elif any(keyword in name_lower for keyword in ["receivable", "inventory", "payable", "accrued"]):
            return "working_capital_change"
        else:
            return "operating_adjustment"
    
    # Investing activity categories
    elif current_activity == "investing":
        if any(keyword in name_lower for keyword in ["expenditure", "capex", "property", "equipment"]):
            return "capital_expenditure"
        elif any(keyword in name_lower for keyword in ["acquisition", "purchase", "investment"]):
            return "acquisition"
        elif "proceeds" in name_lower:
            return "asset_disposal"
        else:
            return "investing_activity"
    
    # Financing activity categories
    elif current_activity == "financing":
        if any(keyword in name_lower for keyword in ["repurchase", "buyback"]):
            return "share_repurchase"
        elif "dividend" in name_lower:
            return "dividend_payment"
        elif any(keyword in name_lower for keyword in ["borrowing", "debt", "loan"]):
            return "debt_activity"
        elif "issuance" in name_lower:
            return "equity_issuance"
        else:
            return "financing_activity"
    
    # Supplemental and reconciliation
    elif current_activity == "supplemental":
        return "supplemental_info"
    
    else:
        return "cash_reconciliation"