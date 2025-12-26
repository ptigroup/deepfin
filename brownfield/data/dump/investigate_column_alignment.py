#!/usr/bin/env python3

import json

def analyze_raw_text_structure():
    """Analyze the raw text to understand the exact column structure."""
    print("=== RAW TEXT COLUMN STRUCTURE ANALYSIS ===")
    
    with open('/mnt/c/Claude/LLMWhisperer/output/raw/shareholder equity_raw.txt', 'r') as f:
        raw_text = f.read()
    
    lines = raw_text.split('\n')
    
    # Find the header rows
    header_row1 = None
    header_row2 = None
    sample_data_row = None
    
    for i, line in enumerate(lines):
        # First header row with main column names
        if 'Common Stock Outstanding' in line and 'Additional Paid-in Capital' in line:
            header_row1 = line
            header_row1_num = i
            print(f"Header Row 1 (line {i+1}): {line}")
            
        # Second header row with sub-headers
        elif 'Shares' in line and 'Amount' in line and header_row1:
            header_row2 = line
            header_row2_num = i
            print(f"Header Row 2 (line {i+1}): {line}")
            
        # Sample data row (January 26, 2020 - the problematic one)
        elif 'Balances, January 26, 2020' in line:
            sample_data_row = line
            sample_data_row_num = i
            print(f"Sample Data Row (line {i+1}): {line}")
            break
    
    # Parse the column structure from the pipe-separated format
    if header_row1 and header_row2 and sample_data_row:
        print(f"\n=== COLUMN MAPPING ANALYSIS ===")
        
        # Split by | and clean up
        header1_parts = [part.strip() for part in header_row1.split('|')[1:-1]]  # Remove first/last empty parts
        header2_parts = [part.strip() for part in header_row2.split('|')[1:-1]]
        data_parts = [part.strip() for part in sample_data_row.split('|')[1:-1]]
        
        print(f"Header Row 1 parts ({len(header1_parts)}):")
        for i, part in enumerate(header1_parts):
            print(f"  {i:2d}: '{part}'")
            
        print(f"\nHeader Row 2 parts ({len(header2_parts)}):")
        for i, part in enumerate(header2_parts):
            print(f"  {i:2d}: '{part}'")
            
        print(f"\nData Row parts ({len(data_parts)}):")
        for i, part in enumerate(data_parts):
            print(f"  {i:2d}: '{part}'")
            
        # Try to map the logical columns
        print(f"\n=== LOGICAL COLUMN MAPPING ===")
        
        # Expected columns based on the schema
        expected_columns = [
            "Common Stock Outstanding:Shares",
            "Common Stock Outstanding:Amount", 
            "Additional Paid-in Capital:",
            "Treasury Stock:",
            "Accumulated Other Comprehensive Income (Loss):",
            "Retained Earnings:",
            "Total Shareholders' Equity"
        ]
        
        print("Expected vs Actual mapping for January 26, 2020 row:")
        print("Expected: 612, $ 1, $ 7,045, $ (9,814), $ 1, $ 14,971, $ 12,204")
        print(f"Raw data: {', '.join(data_parts[:7])}")
        
        # Show the issue
        if len(data_parts) >= 7:
            print(f"\nPROBLEM IDENTIFIED:")
            print(f"Position 0 (should be Shares): '{data_parts[0]}'")
            print(f"Position 1 (should be Amount): '{data_parts[1]}'")  
            print(f"Position 2 (should be Add. Paid-in): '{data_parts[2]}'")
            print(f"Position 3 (should be Treasury): '{data_parts[3]}'")
            print(f"Position 4 (should be Accum. OCI): '{data_parts[4]}'")
            print(f"Position 5 (should be Retained): '{data_parts[5]}'")
            print(f"Position 6 (should be Total): '{data_parts[6]}'")

def analyze_extracted_vs_expected():
    """Compare what the LLM extracted vs what should be extracted."""
    print(f"\n=== EXTRACTED VS EXPECTED DATA COMPARISON ===")
    
    # Load the current extraction
    with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
        data = json.load(f)
    
    structured_str = data['structured_data']
    if structured_str.startswith('```json'):
        structured_str = structured_str[7:]
    if structured_str.endswith('```'):
        structured_str = structured_str[:-3]
    
    structured_data = json.loads(structured_str)
    
    # Find the January 26, 2020 row
    jan_2020_row = None
    for row in structured_data['equity_rows']:
        if 'January 26, 2020' in row['transaction_description']:
            jan_2020_row = row
            break
    
    if jan_2020_row:
        print(f"LLM Extracted for January 26, 2020:")
        for key, value in jan_2020_row['column_values'].items():
            print(f"  {key}: '{value}'")
        
        print(f"\nExpected values (from PDF inspection):")
        print(f"  Common Stock Outstanding:Shares: '612'")
        print(f"  Common Stock Outstanding:Amount: '$ 1'") 
        print(f"  Additional Paid-in Capital:: '$ 7,045'")
        print(f"  Treasury Stock:: '$ (9,814)'")
        print(f"  Accumulated Other Comprehensive Income (Loss):: '$ 1'")  # This is WRONG in extraction!
        print(f"  Retained Earnings:: '$ 14,971'")  # This should be $ 14,971
        print(f"  Total Shareholders' Equity: '$ 12,204'")  # This is empty in extraction!

if __name__ == "__main__":
    analyze_raw_text_structure()
    analyze_extracted_vs_expected()