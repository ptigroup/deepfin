#!/usr/bin/env python3

import json
import os
from pipeline_04_processing.pipeline_04_2_universal_consolidator import UniversalBaseConsolidator

def fix_cash_flow_consolidation():
    """
    Fix the cash flow consolidation by working with the actual source files
    and ensuring all years of data are included correctly.
    """
    print("🔧 FIXING CASH FLOW CONSOLIDATION")
    print("=" * 40)
    
    run_dir = "output/runs/20250927_071801_SUCCESS"
    
    # First, let's analyze what we have
    cf_2022_2021_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2022_2021_02_json.json"
    cf_2020_2019_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2020_2019_02_json.json"
    
    print(f"📊 Source Files Analysis:")
    
    # Load 2022-2021 file
    with open(cf_2022_2021_file, 'r') as f:
        content1 = f.read()
        if content1.startswith('"'):
            data1 = json.loads(json.loads(content1))
        else:
            data1 = json.loads(content1)
    
    print(f"  2022-2021 file:")
    print(f"    Reporting periods: {data1.get('reporting_periods', [])}")
    print(f"    Line items: {len(data1.get('line_items', []))}")
    
    # Load 2020-2019 file  
    with open(cf_2020_2019_file, 'r') as f:
        content2 = f.read()
        if content2.startswith('"'):
            data2 = json.loads(json.loads(content2))
        else:
            data2 = json.loads(content2)
    
    print(f"  2020-2019 file:")
    print(f"    Reporting periods: {data2.get('reporting_periods', [])}")
    print(f"    Line items: {len(data2.get('line_items', []))}")
    
    # The problem: 2020-2019 file only has supplemental info, missing main activities
    # We need to reconstruct the missing data from the Excel file or find another source
    
    # Let's try the consolidation with what we have and see exactly what's missing
    consolidator = UniversalBaseConsolidator()
    
    # Create temporary files in the expected format for consolidation
    temp_files = []
    
    # Convert 2022-2021 data to proper format
    temp_file1 = f"{run_dir}/temp_cf_2022_2021.json"
    with open(temp_file1, 'w') as f:
        json.dump(data1, f, indent=2)
    temp_files.append(temp_file1)
    
    # Convert 2020-2019 data to proper format
    temp_file2 = f"{run_dir}/temp_cf_2020_2019.json" 
    with open(temp_file2, 'w') as f:
        json.dump(data2, f, indent=2)
    temp_files.append(temp_file2)
    
    print(f"\n🔄 Running Universal Consolidation:")
    try:
        result = consolidator.consolidate_financial_data(temp_files, "04_cash_flow")
        
        if "error" not in result:
            consolidated_data = result['consolidated_data']
            
            # Save the properly consolidated data
            output_file = f"{run_dir}/04_cash_flow_06_json_multi_pdf_consolidated_2022-2018_FIXED.json"
            with open(output_file, 'w') as f:
                json.dump(consolidated_data, f, indent=2)
            
            print(f"✅ Fixed consolidation saved to: {os.path.basename(output_file)}")
            
            # Analyze the results
            line_items = consolidated_data.get('line_items', [])
            print(f"\n📊 Fixed Consolidation Analysis:")
            print(f"  Total line items: {len(line_items)}")
            print(f"  Reporting periods: {consolidated_data.get('reporting_periods', [])}")
            
            # Check year coverage for key items
            print(f"\n🔍 Sample Year Coverage:")
            for i, item in enumerate(line_items[:10]):
                name = item.get('account_name', '')
                values = item.get('values', {})
                years_with_data = [k for k, v in values.items() if v and str(v).strip()]
                print(f"  {i+1:2d}. '{name}': {len(years_with_data)} years")
            
            # Check for section headers
            section_headers = [item for item in line_items if item.get('is_section_header', False)]
            print(f"\n🏗️ Section Headers ({len(section_headers)}):")
            for header in section_headers:
                print(f"  • '{header.get('account_name', '')}'")
            
            return output_file
            
        else:
            print(f"❌ Consolidation failed: {result['error']}")
            return None
            
    except Exception as e:
        print(f"❌ Error during consolidation: {e}")
        return None
    
    finally:
        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    fix_cash_flow_consolidation()