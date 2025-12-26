#!/usr/bin/env python3

import json
import os
from pipeline_04_processing.pipeline_04_2_universal_consolidator import UniversalBaseConsolidator

def final_cash_flow_fix():
    """
    Create the final fixed cash flow consolidation using the reconstructed 2020-2019 data.
    """
    print("🎯 FINAL CASH FLOW CONSOLIDATION FIX")
    print("=" * 45)
    
    run_dir = "output/runs/20250927_071801_SUCCESS"
    
    # Use the good 2022-2021 file and the reconstructed 2020-2019 file
    cf_2022_2021_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2022_2021_02_json.json"
    cf_2020_2019_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2020_2019_02_json_RECONSTRUCTED.json"
    
    print("📊 Using Files:")
    print(f"  2022-2021: {os.path.basename(cf_2022_2021_file)}")
    print(f"  2020-2019: {os.path.basename(cf_2020_2019_file)} (reconstructed)")
    
    # Load both files in the correct format for consolidation
    source_files = [cf_2022_2021_file, cf_2020_2019_file]
    
    # Run the consolidation
    consolidator = UniversalBaseConsolidator()
    
    print(f"\n🔄 Running Final Consolidation...")
    try:
        result = consolidator.consolidate_financial_data(source_files, "04_cash_flow")
        
        if "error" not in result:
            consolidated_data = result['consolidated_data']
            
            # Save the final fixed consolidation
            output_file = f"{run_dir}/04_cash_flow_06_json_multi_pdf_consolidated_2022-2018_FINAL_FIXED.json"
            with open(output_file, 'w') as f:
                json.dump(consolidated_data, f, indent=2)
            
            print(f"✅ Final fixed consolidation saved!")
            
            # Comprehensive analysis
            line_items = consolidated_data.get('line_items', [])
            reporting_periods = consolidated_data.get('reporting_periods', [])
            
            print(f"\n📊 FINAL CONSOLIDATION ANALYSIS:")
            print(f"  Reporting periods: {reporting_periods}")
            print(f"  Total line items: {len(line_items)}")
            
            # Check for all major section headers
            section_headers = [item for item in line_items if item.get('is_section_header', False)]
            critical_headers = [
                'Cash flows from operating activities:',
                'Cash flows from investing activities:',
                'Cash flows from financing activities:'
            ]
            
            print(f"\n🏗️ SECTION HEADERS CHECK:")
            found_critical = []
            for header in section_headers:
                header_name = header.get('account_name', '')
                for critical in critical_headers:
                    if critical.lower() in header_name.lower():
                        found_critical.append(header_name)
                        print(f"  ✅ '{header_name}'")
            
            missing_critical = set(critical_headers) - set(found_critical)
            if missing_critical:
                for missing in missing_critical:
                    print(f"  ❌ Missing: '{missing}'")
            else:
                print(f"  🎉 All critical section headers found!")
            
            # Check year coverage for sample items
            print(f"\n📈 YEAR COVERAGE ANALYSIS:")
            items_with_5_years = 0
            items_with_3_years = 0
            items_with_less = 0
            
            for item in line_items:
                if not item.get('is_section_header', False):  # Skip headers
                    values = item.get('values', {})
                    years_with_data = len([v for v in values.values() if v and str(v).strip()])
                    
                    if years_with_data >= 5:
                        items_with_5_years += 1
                    elif years_with_data >= 3:
                        items_with_3_years += 1
                    else:
                        items_with_less += 1
            
            total_data_items = items_with_5_years + items_with_3_years + items_with_less
            
            print(f"  Items with 5 years data: {items_with_5_years}/{total_data_items}")
            print(f"  Items with 3+ years data: {items_with_3_years}/{total_data_items}")
            print(f"  Items with <3 years data: {items_with_less}/{total_data_items}")
            
            # Show sample of key accounts with year coverage
            print(f"\n🔍 KEY ACCOUNTS YEAR COVERAGE:")
            key_accounts = ['Net income', 'Stock-based compensation expense', 'Dividends paid', 'Change in cash and cash equivalents']
            
            for item in line_items:
                name = item.get('account_name', '')
                if any(key.lower() in name.lower() for key in key_accounts):
                    values = item.get('values', {})
                    years_with_data = [k for k, v in values.items() if v and str(v).strip()]
                    print(f"  • '{name}': {len(years_with_data)} years")
                    if len(years_with_data) < 4:  # Should have 4-5 years
                        print(f"    Years: {[k.split()[-1] for k in years_with_data]}")
            
            return output_file
            
        else:
            print(f"❌ Consolidation failed: {result['error']}")
            return None
            
    except Exception as e:
        print(f"❌ Error during final consolidation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    final_cash_flow_fix()