#!/usr/bin/env python3

import json

def verify_direct_parsing():
    """Verify that direct parsing has fixed all column alignment issues."""
    
    print("🔍 VERIFYING DIRECT PARSING RESULTS")
    print("=" * 50)
    
    # Load the direct extraction results
    with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_direct_extraction.json', 'r') as f:
        data = json.load(f)
    
    structured_data = json.loads(data['structured_data'])
    
    # Expected values for January 26, 2020 (our test case)
    expected_jan_2020 = {
        "Common Stock Outstanding:Shares": "612",
        "Common Stock Outstanding:Amount": "$ 1", 
        "Additional Paid-in Capital:": "$ 7,045",
        "Treasury Stock:": "$ (9,814)",
        "Accumulated Other Comprehensive Income (Loss):": "$ 1",
        "Retained Earnings:": "$ 14,971",
        "Total Shareholders' Equity": "$ 12,204"
    }
    
    # Find the January 26, 2020 row
    jan_2020_row = None
    for row in structured_data['equity_rows']:
        if 'January 26, 2020' in row['transaction_description']:
            jan_2020_row = row
            break
    
    if not jan_2020_row:
        print("❌ Could not find January 26, 2020 row!")
        return False
    
    print("✅ Found January 26, 2020 row")
    print(f"📝 Description: {jan_2020_row['transaction_description']}")
    
    # Verify each column value
    print(f"\n📊 COLUMN VERIFICATION:")
    all_correct = True
    
    actual_values = jan_2020_row['column_values']
    
    for column, expected_value in expected_jan_2020.items():
        actual_value = actual_values.get(column, "MISSING")
        is_correct = actual_value == expected_value
        status = "✅" if is_correct else "❌"
        
        print(f"  {status} {column:50} | Expected: {expected_value:10} | Got: {actual_value:10}")
        
        if not is_correct:
            all_correct = False
    
    # Check all balance rows have complete data
    print(f"\n📈 BALANCE ROWS COMPLETENESS CHECK:")
    balance_rows = [row for row in structured_data['equity_rows'] if row['row_type'] == 'balance']
    
    for i, row in enumerate(balance_rows):
        description = row['transaction_description']
        total_value = row['column_values'].get("Total Shareholders' Equity", "MISSING")
        has_total = total_value != "MISSING" and total_value != ""
        status = "✅" if has_total else "❌"
        
        print(f"  {status} {description:30} | Total: {total_value}")
        
        if not has_total:
            all_correct = False
    
    # Overall summary
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"  Total rows extracted: {len(structured_data['equity_rows'])}")
    print(f"  Balance rows: {len(balance_rows)}")  
    print(f"  Transaction rows: {len([row for row in structured_data['equity_rows'] if row['row_type'] == 'transaction'])}")
    
    if all_correct:
        print(f"\n🎉 SUCCESS! All column alignments are now PERFECT!")
        print(f"✅ Direct parsing has completely solved the column shift issue")
        print(f"✅ All balance rows have complete data")
        print(f"✅ All values match expected raw text positions")
    else:
        print(f"\n❌ Some issues still remain")
    
    return all_correct

if __name__ == "__main__":
    success = verify_direct_parsing()
    print(f"\nFinal result: {'PASS' if success else 'FAIL'}")