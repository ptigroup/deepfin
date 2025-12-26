#!/usr/bin/env python3

import json

def load_structured_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    structured_str = data['structured_data']
    if structured_str.startswith('```json'):
        structured_str = structured_str[7:]
    if structured_str.endswith('```'):
        structured_str = structured_str[:-3]
    
    return json.loads(structured_str)

# Load both versions
working = load_structured_data('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder_equity_schema_test.json')
problem = load_structured_data('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json')

print("=== BALANCE ROWS COMPARISON ===")
working_balances = [row for row in working['equity_rows'] if 'Balance' in row['transaction_description']]
problem_balances = [row for row in problem['equity_rows'] if 'Balance' in row['transaction_description']]

print(f"Working version balance rows: {len(working_balances)}")
for row in working_balances:
    print(f"  {row['transaction_description']}")

print(f"\nProblem version balance rows: {len(problem_balances)}")  
for row in problem_balances:
    print(f"  {row['transaction_description']}")

# Check the 2017 balance specifically
print(f"\n=== 2017 BALANCE ROW COMPARISON ===")
working_2017 = next((row for row in working['equity_rows'] if 'January 29, 2017' in row['transaction_description']), None)
problem_2017 = next((row for row in problem['equity_rows'] if 'January 29, 2017' in row['transaction_description']), None)

if working_2017 and problem_2017:
    print("WORKING 2017 VALUES:")
    for key, value in working_2017['column_values'].items():
        print(f"  {key}: '{value}'")
    
    print("\nPROBLEM 2017 VALUES:")
    for key, value in problem_2017['column_values'].items():
        print(f"  {key}: '{value}'")
        
    print("\n=== KEY DIFFERENCES ===")
    working_keys = set(working_2017['column_values'].keys())
    problem_keys = set(problem_2017['column_values'].keys())
    
    if working_keys != problem_keys:
        print(f"Key differences detected!")
        print(f"Working keys: {working_keys}")
        print(f"Problem keys: {problem_keys}")
        print(f"Missing from problem: {working_keys - problem_keys}")
        print(f"Extra in problem: {problem_keys - working_keys}")
    else:
        print("Keys are identical")
        
    # Check if values are misaligned
    print(f"\n=== VALUE ALIGNMENT CHECK ===")
    expected_order = [
        "Common Stock Outstanding:Shares",
        "Common Stock Outstanding:Amount", 
        "Additional Paid-in Capital:",
        "Treasury Stock:",
        "Accumulated Other Comprehensive Income (Loss):",
        "Retained Earnings:",
        "Total Shareholders' Equity"
    ]
    
    for key in expected_order:
        working_val = working_2017['column_values'].get(key, 'MISSING')
        problem_val = problem_2017['column_values'].get(key, 'MISSING')
        if key.endswith(':'):
            problem_val_alt = problem_2017['column_values'].get(key[:-1], 'MISSING')
            if problem_val == 'MISSING' and problem_val_alt != 'MISSING':
                problem_val = problem_val_alt
        print(f"{key:50} | Working: {working_val:10} | Problem: {problem_val}")