#!/usr/bin/env python3

import json
from schemas.excel_exporter import SchemaBasedExcelExporter
from schemas import schema_registry
from schemas.base_schema import FinancialStatementType

def debug_excel_headers():
    """Debug Excel header generation."""
    
    print("🔍 DEBUGGING EXCEL HEADERS")
    print("=" * 50)
    
    # Load the JSON data
    with open('/mnt/c/Claude/LLMWhisperer/output/structured/json/shareholder equity_schema_based_extraction.json', 'r') as f:
        data = json.load(f)
    
    # Parse the structured data
    financial_data = json.loads(data['structured_data'])
    
    # Get schema class
    schema_class = schema_registry.get_schema_class(FinancialStatementType.SHAREHOLDERS_EQUITY)
    
    print(f"✅ Schema class: {schema_class.__name__}")
    
    # Create schema instance
    schema_instance = schema_class.model_validate(financial_data)
    print(f"✅ Schema instance created successfully")
    
    # Get layout configuration
    layout_config = schema_instance.get_excel_layout_config()
    
    print(f"\n📊 LAYOUT CONFIG:")
    print(f"Header rows: {layout_config.header_rows}")
    print(f"Has multi-level headers: {layout_config.has_multi_level_headers}")
    print(f"Table start row: {layout_config.table_start_row}")
    print(f"Data start row: {layout_config.data_start_row}")
    print(f"Number of column mappings: {len(layout_config.column_mappings)}")
    
    print(f"\n📝 COLUMN MAPPINGS:")
    for i, mapping in enumerate(layout_config.column_mappings):
        print(f"  {i+1}: Excel Col {mapping.excel_column_index} -> '{mapping.main_header}' : '{mapping.sub_header}' (merge_with_next: {mapping.merge_with_next})")
    
    print(f"\n💡 SAMPLE DATA KEYS:")
    if financial_data.get('equity_rows'):
        sample_row = financial_data['equity_rows'][0]
        print(f"  Sample row description: {sample_row['transaction_description']}")
        print(f"  Sample column_values keys:")
        for key, value in sample_row['column_values'].items():
            print(f"    '{key}' -> '{value}'")

if __name__ == "__main__":
    debug_excel_headers()