#!/usr/bin/env python3

import json

# Read the WORKING extraction
with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder_equity_schema_test.json', 'r') as f:
    data = json.load(f)

# Parse the structured_data string
structured_str = data['structured_data']
structured_data = json.loads(structured_str)

print("=== WORKING EXTRACTION COLUMN HEADERS ===")
for i, header in enumerate(structured_data['column_headers']):
    main = header['main_header']
    sub = header.get('sub_header', '')
    idx = header['column_index']
    print(f"{i+1}: main='{main}', sub='{sub}', index={idx}")

print("\n=== WORKING FIRST DATA ROW SAMPLE ===")
first_row = structured_data['equity_rows'][0]
print(f"Description: {first_row['transaction_description']}")
print("Column values:")
for key, value in first_row['column_values'].items():
    print(f"  {key}: {value}")

print(f"\n=== ROW COUNT COMPARISON ===")
print(f"Working version rows: {len(structured_data['equity_rows'])}")

with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
    prob_data = json.load(f)
prob_structured_str = prob_data['structured_data']
if prob_structured_str.startswith('```json'):
    prob_structured_str = prob_structured_str[7:]
if prob_structured_str.endswith('```'):
    prob_structured_str = prob_structured_str[:-3]
prob_structured_data = json.loads(prob_structured_str)
print(f"Problem version rows: {len(prob_structured_data['equity_rows'])}")