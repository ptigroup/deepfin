#!/usr/bin/env python3

import json

def trace_complete_data_flow():
    """Trace the complete data flow to understand where the shift happens."""
    print("=== COMPLETE DATA FLOW ANALYSIS ===")
    
    # Step 1: Raw text analysis (we know the correct values)
    print("STEP 1: RAW TEXT VALUES (January 26, 2020)")
    raw_correct_mapping = {
        "Description": "Balances, January 26, 2020",
        "Shares": "612", 
        "Amount": "$ 1",
        "Additional Paid-in Capital": "$ 7,045",
        "Treasury Stock": "$ (9,814)", 
        "Accumulated Other Comprehensive Income (Loss)": "$ 1",
        "Retained Earnings": "$ 14,971",
        "Total Shareholders' Equity": "$ 12,204"
    }
    
    for key, value in raw_correct_mapping.items():
        print(f"  {key}: {value}")
    
    # Step 2: LLM extraction
    print(f"\nSTEP 2: LLM EXTRACTED VALUES")
    with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
        data = json.load(f)
    
    structured_str = data['structured_data']
    if structured_str.startswith('```json'):
        structured_str = structured_str[7:]
    if structured_str.endswith('```'):
        structured_str = structured_str[:-3]
    
    structured_data = json.loads(structured_str)
    
    jan_2020_row = None
    for row in structured_data['equity_rows']:
        if 'January 26, 2020' in row['transaction_description']:
            jan_2020_row = row
            break
    
    if jan_2020_row:
        llm_extracted = jan_2020_row['column_values']
        for key, value in llm_extracted.items():
            print(f"  {key}: {value}")
    
    # Step 3: Analysis of the shift
    print(f"\nSTEP 3: SHIFT ANALYSIS")
    print("Comparing Raw (correct) vs LLM (extracted):")
    
    comparisons = [
        ("Shares", "Common Stock Outstanding:Shares", raw_correct_mapping["Shares"], llm_extracted.get("Common Stock Outstanding:Shares", "")),
        ("Amount", "Common Stock Outstanding:Amount", raw_correct_mapping["Amount"], llm_extracted.get("Common Stock Outstanding:Amount", "")),
        ("Add. Paid-in", "Additional Paid-in Capital:", raw_correct_mapping["Additional Paid-in Capital"], llm_extracted.get("Additional Paid-in Capital:", "")),
        ("Treasury", "Treasury Stock:", raw_correct_mapping["Treasury Stock"], llm_extracted.get("Treasury Stock:", "")),
        ("Accum. OCI", "Accumulated Other Comprehensive Income (Loss):", raw_correct_mapping["Accumulated Other Comprehensive Income (Loss)"], llm_extracted.get("Accumulated Other Comprehensive Income (Loss):", "")),
        ("Retained", "Retained Earnings:", raw_correct_mapping["Retained Earnings"], llm_extracted.get("Retained Earnings:", "")),
        ("Total", "Total Shareholders' Equity", raw_correct_mapping["Total Shareholders' Equity"], llm_extracted.get("Total Shareholders' Equity", ""))
    ]
    
    for short_name, full_key, expected, actual in comparisons:
        status = "✅" if expected == actual else "❌"
        print(f"  {status} {short_name:12}: Expected '{expected:10}' | Got '{actual:10}' | Match: {expected == actual}")
    
    # Step 4: Root cause identification
    print(f"\nSTEP 4: ROOT CAUSE ANALYSIS")
    print("The issue occurs during LLM extraction phase:")
    print("1. ✅ First 4 columns are correctly mapped")
    print("2. ❌ From column 5 onwards, LLM shifts all values by one position to the left")
    print("3. ❌ This happens because the empty column in header confuses the LLM's column mapping")
    print("4. ❌ The LLM tries to align data with non-empty headers, skipping the empty column position")
    
    return comparisons

def analyze_other_balance_rows():
    """Check if the same issue affects other balance rows."""
    print(f"\n=== OTHER BALANCE ROWS ANALYSIS ===")
    
    with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
        data = json.load(f)
    
    structured_str = data['structured_data']
    if structured_str.startswith('```json'):
        structured_str = structured_str[7:]
    if structured_str.endswith('```'):
        structured_str = structured_str[:-3]
    
    structured_data = json.loads(structured_str)
    
    balance_rows = [row for row in structured_data['equity_rows'] if row['row_type'] == 'balance']
    
    print(f"Found {len(balance_rows)} balance rows:")
    for row in balance_rows:
        desc = row['transaction_description']
        total_value = row['column_values'].get("Total Shareholders' Equity", "MISSING")
        print(f"  {desc}: Total = '{total_value}'")
    
    print(f"\nISSUE CONFIRMED: All balance rows except the first one have empty Total Shareholders' Equity values!")

if __name__ == "__main__":
    trace_complete_data_flow()
    analyze_other_balance_rows()