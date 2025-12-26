#!/usr/bin/env python3
"""
Convert successfully extracted JSON data to Financial Excel format
This bypasses the LLMWhisperer timeout issues by using our working structured data
"""

import json
import pandas as pd
import sys
from pathlib import Path

def convert_json_to_financial_excel(json_file_path, output_excel_path):
    """
    Convert structured JSON financial data to Excel format matching financial_table_extractor.py output.
    
    Args:
        json_file_path (str): Path to the structured JSON file
        output_excel_path (str): Path for the output Excel file
    """
    
    print(f"📄 Converting: {json_file_path}")
    print(f"📊 Output: {output_excel_path}")
    
    try:
        # Load the JSON data
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Extract the structured data from the JSON
        extracted_data_str = data.get('extracted_data', '')
        
        # Parse the JSON from the extracted_data field (it's wrapped in ```json blocks)
        if extracted_data_str.startswith('```json'):
            json_start = extracted_data_str.find('{')
            json_end = extracted_data_str.rfind('}') + 1
            financial_data = json.loads(extracted_data_str[json_start:json_end])
        else:
            financial_data = json.loads(extracted_data_str)
        
        # Convert to DataFrame
        line_items = financial_data.get('line_items', [])
        
        if not line_items:
            print("❌ No line items found in the structured data")
            return False
        
        # Create DataFrame from line items
        df = pd.DataFrame(line_items)
        
        # Add metadata sheet
        metadata = {
            'Document Title': [financial_data.get('document_title', 'Unknown')],
            'Document Type': [data.get('document_type', 'unknown')],
            'Schema Used': [data.get('schema_used', 'unknown')],
            'Processing Time': [f"{data.get('processing_time', 0):.2f} seconds"],
            'Extraction Timestamp': [data.get('extraction_timestamp', 'unknown')],
            'Reporting Periods': [', '.join(financial_data.get('reporting_periods', []))]
        }
        metadata_df = pd.DataFrame(metadata)
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
            # Write the main financial data
            df.to_excel(writer, sheet_name='Financial Data', index=False)
            
            # Write metadata
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        print(f"✅ Successfully converted to Excel!")
        print(f"📊 Rows: {len(df)}")
        print(f"📋 Columns: {list(df.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting JSON to Excel: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python json_to_financial_excel.py <input_json> <output_excel>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    excel_file = sys.argv[2]
    
    if not Path(json_file).exists():
        print(f"❌ JSON file not found: {json_file}")
        sys.exit(1)
    
    success = convert_json_to_financial_excel(json_file, excel_file)
    
    if success:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📄 Excel file saved: {excel_file}")
    else:
        print(f"\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()