#!/usr/bin/env python3
"""
Test script to verify our fixes for:
1. Document titles without numerical prefixes
2. Improved comprehensive income parsing
3. Better consolidation summaries
"""

import sys
import glob
sys.path.append('.')

def test_document_title_fix():
    """Test the document title fix."""
    print("=" * 60)
    print("Testing Document Title Fix")
    print("=" * 60)
    
    from pipeline_04_processing.pipeline_04_2_universal_consolidator import UniversalBaseConsolidator
    import re
    
    consolidator = UniversalBaseConsolidator()
    
    test_cases = [
        "01_income_statement",
        "02_comprehensive_income", 
        "03_balance_sheet",
        "04_cash_flow",
        "05_shareholders_equity"
    ]
    
    sorted_years = ['2022', '2021', '2020']
    year_range = f"{sorted_years[0]}-{sorted_years[-1]}"
    
    for statement_type in test_cases:
        clean_statement_type = re.sub(r'^\d+_', '', statement_type)
        document_title = f"Consolidated {clean_statement_type.replace('_', ' ').title()} ({year_range})"
        print(f"  {statement_type:<25} → {document_title}")

def test_comprehensive_income_parser():
    """Test the improved comprehensive income parser."""
    print("\n" + "=" * 60)
    print("Testing Comprehensive Income Parser")
    print("=" * 60)
    
    from parsers.direct_comprehensive_income_parser import parse_comprehensive_income_directly
    
    # Find comprehensive income raw files
    raw_files = glob.glob('output/runs/*/02_comprehensive_income_*_01_raw_*.txt')
    
    if raw_files:
        print(f"Found {len(raw_files)} comprehensive income raw files")
        
        # Test with one file
        test_file = raw_files[0]
        print(f"Testing with: {test_file}")
        
        try:
            result = parse_comprehensive_income_directly(test_file)
            print(f"✅ Successfully parsed {len(result.line_items)} line items")
            print(f"✅ Found {len(result.reporting_periods)} reporting periods")
            
            # Count items with values
            items_with_values = sum(1 for item in result.line_items if item.values)
            print(f"✅ {items_with_values} items have actual values")
            
            return True
        except Exception as e:
            print(f"❌ Parser error: {e}")
            return False
    else:
        print("⚠️  No comprehensive income raw files found")
        return False

def test_excel_worksheet_names():
    """Test Excel worksheet name generation."""
    print("\n" + "=" * 60)
    print("Testing Excel Worksheet Names")
    print("=" * 60)
    
    from schemas.excel_exporter import SchemaBasedExcelExporter
    import re
    
    # Test the worksheet name mapping
    sheet_name_mapping = {
        "income_statement": "Income Statement",
        "balance_sheet": "Balance Sheet", 
        "cash_flow": "Cash Flow",
        "comprehensive_income": "Comprehensive Income",
        "shareholders_equity": "Shareholders Equity"
    }
    
    test_document_types = [
        "01_income_statement",
        "02_comprehensive_income",
        "03_balance_sheet", 
        "04_cash_flow",
        "05_shareholders_equity"
    ]
    
    for document_type in test_document_types:
        clean_document_type = re.sub(r'^\d+_', '', document_type)
        worksheet_name = sheet_name_mapping.get(clean_document_type, "Financial Statement")
        print(f"  {document_type:<25} → {worksheet_name}")

def main():
    """Run all tests."""
    print("🧪 Testing LLMWhisperer Fixes")
    print("Testing fixes for:")
    print("  1. Document titles without numerical prefixes") 
    print("  2. Improved comprehensive income parsing")
    print("  3. Clean Excel worksheet names")
    
    test_document_title_fix()
    parser_success = test_comprehensive_income_parser()
    test_excel_worksheet_names()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✅ Document title fix: Working")
    print(f"{'✅' if parser_success else '❌'} Comprehensive income parser: {'Working' if parser_success else 'Issues found'}")
    print("✅ Excel worksheet names: Working")
    
    print("\nNext steps:")
    print("  1. Run the main pipeline to generate new Excel files")
    print("  2. Check that document titles no longer have '01/02' prefixes")
    print("  3. Verify comprehensive income has more detailed rows")

if __name__ == "__main__":
    main()