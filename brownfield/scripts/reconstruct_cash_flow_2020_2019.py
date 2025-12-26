#!/usr/bin/env python3

import json
import re
from pipeline_03_extraction.pipeline_03_2_schema_processor import process_with_direct_parsing
from schemas.cash_flow_schema import CashFlowSchema

def reconstruct_cash_flow_2020_2019():
    """
    Reconstruct the missing cash flow data for 2020-2019 by reprocessing 
    the raw text files with the direct cash flow parser.
    """
    print("🔧 RECONSTRUCTING CASH FLOW 2020-2019")
    print("=" * 45)
    
    run_dir = "output/runs/20250927_071801_SUCCESS"
    
    # Combine the raw text from both pages
    page43_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2020_2019_01_raw_page43.txt"
    page44_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2020_2019_01_raw_page44.txt"
    
    print("📖 Reading raw text files...")
    
    # Read both pages
    with open(page43_file, 'r') as f:
        page43_content = f.read()
    
    with open(page44_file, 'r') as f:
        page44_content = f.read()
    
    # Combine the content (page 43 has main activities, page 44 has supplemental)
    combined_content = page43_content + "\n\n" + page44_content
    
    # Create a temporary combined raw file
    combined_raw_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2020_2019_01_raw_COMBINED.txt"
    with open(combined_raw_file, 'w') as f:
        f.write(combined_content)
    
    print(f"📝 Combined raw text: {len(combined_content)} characters")
    
    # Now process with the direct cash flow parser
    print("⚙️ Processing with direct cash flow parser...")
    
    try:
        structured_data = process_with_direct_parsing(
            combined_raw_file,
            "/mnt/c/Claude/LLMWhisperer/input/NVIDIA 10K 2020-2019.pdf",
            CashFlowSchema
        )
        
        if structured_data:
            print("✅ Direct parsing successful!")
            
            # Save the reconstructed JSON
            output_file = f"{run_dir}/04_cash_flow_NVIDIA_10K_2020_2019_02_json_RECONSTRUCTED.json"
            
            # Handle the structured_data format
            if hasattr(structured_data, 'dict'):
                data_dict = structured_data.dict()
            elif isinstance(structured_data, dict):
                data_dict = structured_data
            else:
                # structured_data might already be a JSON string
                try:
                    data_dict = json.loads(structured_data) if isinstance(structured_data, str) else structured_data
                except:
                    data_dict = structured_data
            
            # Save in the same format as the original file (JSON string)
            with open(output_file, 'w') as f:
                json.dump(json.dumps(data_dict), f, indent=2)
            
            print(f"💾 Reconstructed data saved to: {output_file}")
            
            # Analyze the reconstructed data
            line_items = data_dict.get('line_items', [])
            reporting_periods = data_dict.get('reporting_periods', [])
            
            print(f"\n📊 Reconstructed Data Analysis:")
            print(f"  Reporting periods: {reporting_periods}")
            print(f"  Total line items: {len(line_items)}")
            
            # Check for main section headers
            section_headers = [item for item in line_items if item.get('is_section_header', False)]
            print(f"  Section headers: {len(section_headers)}")
            
            # Look for the missing headers specifically
            missing_headers = ['Cash flows from investing activities:', 'Cash flows from financing activities:']
            found_headers = []
            for header in section_headers:
                header_name = header.get('account_name', '')
                for missing in missing_headers:
                    if missing.lower() in header_name.lower():
                        found_headers.append(header_name)
            
            print(f"  Found critical headers: {len(found_headers)}")
            for header in found_headers:
                print(f"    • '{header}'")
            
            # Check sample year coverage
            print(f"\n🔍 Sample Year Coverage:")
            for i, item in enumerate(line_items[:10]):
                name = item.get('account_name', '')
                values = item.get('values', {})
                years_with_data = [k for k, v in values.items() if v and str(v).strip()]
                print(f"  {i+1:2d}. '{name}': {len(years_with_data)} years")
            
            return output_file
            
        else:
            print("❌ Direct parsing failed")
            return None
            
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Clean up temp file
        import os
        if os.path.exists(combined_raw_file):
            os.remove(combined_raw_file)

if __name__ == "__main__":
    reconstruct_cash_flow_2020_2019()