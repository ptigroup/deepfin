#!/usr/bin/env python3

from pipeline_04_processing.pipeline_04_2_universal_consolidator import UniversalBaseConsolidator
import glob
import json

def test_comprehensive_income_consolidation():
    consolidator = UniversalBaseConsolidator()
    
    # Find comprehensive income JSON files in latest run
    comp_files = glob.glob('output/runs/20250927_062653_SUCCESS/02_comprehensive_income_*_02_json.json')
    print(f'Found {len(comp_files)} comprehensive income files')
    
    if len(comp_files) >= 2:
        result = consolidator.consolidate_financial_data(comp_files, '02_comprehensive_income')
        
        if 'error' not in result:
            print('Consolidation successful!')
            data = result['consolidated_data']
            print(f'Line items: {len(data.get("line_items", []))}')
            
            # Check for duplicates
            names_and_parents = []
            for item in data.get('line_items', []):
                name = item.get('account_name', '')
                parent = item.get('parent_section', '')
                names_and_parents.append((name, parent))
            
            unique_pairs = set(names_and_parents)
            print(f'Unique name+parent pairs: {len(unique_pairs)}')
            print(f'Total line items: {len(names_and_parents)}')
            
            if len(unique_pairs) != len(names_and_parents):
                print('ISSUE: Duplicate entries found!')
                from collections import Counter
                counts = Counter(names_and_parents)
                for (name, parent), count in counts.items():
                    if count > 1:
                        print(f'  Duplicate: "{name}" (parent: "{parent}") appears {count} times')
            else:
                print('SUCCESS: No duplicates found!')
                
            # Save the fixed result
            output_path = 'output/02_comprehensive_income_06_json_multi_pdf_consolidated_2022-2018_FIXED.json'
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f'Fixed consolidation saved to: {output_path}')
            
        else:
            print(f'Error: {result["error"]}')
    else:
        print('Not enough files for consolidation')

if __name__ == "__main__":
    test_comprehensive_income_consolidation()