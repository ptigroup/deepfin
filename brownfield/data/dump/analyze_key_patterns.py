#!/usr/bin/env python3

import json

def analyze_keys(file_path, label):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    structured_str = data['structured_data']
    if structured_str.startswith('```json'):
        structured_str = structured_str[7:]
    if structured_str.endswith('```'):
        structured_str = structured_str[:-3]
    
    structured_data = json.loads(structured_str)
    
    print(f"=== {label} KEY PATTERNS ===")
    
    # Get unique keys across all rows
    all_keys = set()
    for row in structured_data['equity_rows']:
        all_keys.update(row['column_values'].keys())
    
    # Categorize keys
    multi_column_keys = []
    single_column_keys = []
    
    for key in sorted(all_keys):
        if ':' in key and not key.endswith(':'):
            # Has colon and something after it (multi-column)
            multi_column_keys.append(key)
        else:
            # No colon or ends with colon (single column)
            single_column_keys.append(key)
    
    print(f"Multi-column keys ({len(multi_column_keys)}):")
    for key in multi_column_keys:
        print(f"  '{key}'")
    
    print(f"Single-column keys ({len(single_column_keys)}):")
    for key in single_column_keys:
        print(f"  '{key}'")
    
    return all_keys

# Analyze both versions
working_keys = analyze_keys('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder_equity_schema_test.json', 'WORKING')
problem_keys = analyze_keys('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'PROBLEM')

print(f"\n=== PATTERN ANALYSIS ===")
print(f"Working: {working_keys}")
print(f"Problem: {problem_keys}")

# Check for the specific Total Shareholders' Equity key
working_total_key = [k for k in working_keys if 'Total Shareholders' in k]
problem_total_key = [k for k in problem_keys if 'Total Shareholders' in k]

print(f"\nTotal Shareholders' Equity key:")
print(f"Working: {working_total_key}")
print(f"Problem: {problem_total_key}")