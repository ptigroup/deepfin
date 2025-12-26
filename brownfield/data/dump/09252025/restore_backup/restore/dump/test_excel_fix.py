#!/usr/bin/env python3

import json
from schemas.excel_exporter import SchemaBasedExcelExporter
from schemas import schema_registry
from schemas.base_schema import FinancialStatementType

def test_excel_fix():
    """Test that the Excel export works correctly with proper schema-based exporter."""
    
    print("🧪 TESTING FIXED EXCEL EXPORT")
    print("=" * 50)
    
    # Load the JSON data
    with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
        data = json.load(f)
    
    # Parse the structured data
    financial_data = json.loads(data['structured_data'])
    
    # Get schema class
    schema_class = schema_registry.get_schema_class(FinancialStatementType.SHAREHOLDERS_EQUITY)
    
    print(f"✅ Schema class: {schema_class.__name__}")
    
    try:
        # Create schema instance using the fixed method
        schema_instance = schema_class.model_validate(financial_data)
        print(f"✅ Schema instance created successfully")
        
        # Use the schema-based Excel exporter
        output_path = 'output/structured/excel/test_fixed_export.xlsx'
        exporter = SchemaBasedExcelExporter()
        
        print(f"🚀 Exporting to: {output_path}")
        exporter.export_to_excel(schema_instance, output_path)
        
        print(f"✅ Excel export completed successfully!")
        
        # Verify the Excel file - read with proper header row
        import pandas as pd
        df = pd.read_excel(output_path, header=[1, 2])  # Multi-level headers in rows 1 and 2 (0-indexed)
        
        print(f"\n📊 EXCEL VERIFICATION:")
        print(f"Columns: {list(df.columns)}")
        
        # Look for Total Shareholders' Equity column
        total_col = None
        for col in df.columns:
            if "Total" in str(col) and "Equity" in str(col):
                total_col = col
                break
                
        if total_col:
            non_empty_values = df[total_col].dropna()
            print(f"✅ Found Total Shareholders' Equity column: '{total_col}'")
            print(f"✅ Non-empty values: {len(non_empty_values)}")
            
            # Show sample values
            if len(non_empty_values) > 0:
                print(f"Sample total values:")
                for i, (idx, value) in enumerate(non_empty_values.head().items()):
                    desc_col = df.columns[0] if len(df.columns) > 0 else 'Unknown'
                    desc = df.loc[idx, desc_col] if desc_col in df.columns else 'N/A'
                    print(f"  {i+1}: {str(desc)[:40]:40} | Total: {value}")
            else:
                print("❌ No values in Total column")
        else:
            print(f"❌ Total Shareholders' Equity column not found")
            print(f"Available columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_fix()