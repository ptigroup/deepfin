#!/usr/bin/env python3

import json

# Read the problematic extraction
with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
    data = json.load(f)

# Parse the structured_data string
structured_str = data['structured_data']
if structured_str.startswith('```json'):
    structured_str = structured_str[7:]
if structured_str.endswith('```'):
    structured_str = structured_str[:-3]
    
structured_data = json.loads(structured_str)

print("=== CURRENT EXTRACTION COLUMN HEADERS ===")
for i, header in enumerate(structured_data['column_headers']):
    main = header['main_header']
    sub = header.get('sub_header', '')
    idx = header['column_index']
    print(f"{i+1}: main='{main}', sub='{sub}', index={idx}")

print("\n=== FIRST DATA ROW SAMPLE ===")
first_row = structured_data['equity_rows'][0]
print(f"Description: {first_row['transaction_description']}")
print("Column values:")
for key, value in first_row['column_values'].items():
    print(f"  {key}: {value}")

print("\n=== EXPECTED STRUCTURE FROM RAW TEXT ===")
print("Based on raw text analysis:")
print("1. Common Stock Outstanding:Shares")
print("2. Common Stock Outstanding:Amount") 
print("3. Additional Paid-in Capital:")
print("4. Treasury Stock:")
print("5. Accumulated Other Comprehensive Income (Loss):")
print("6. Retained Earnings:")
print("7. Total Shareholders' Equity:")