#!/usr/bin/env python3

import json
import re
from datetime import datetime
from pathlib import Path
from pipeline_logger import logger

def parse_shareholders_equity_directly(raw_text_file_path):
    """
    Direct parser for shareholders equity that bypasses LLM interpretation.
    Maps data by exact position from pipe-separated table structure.
    """
    
    with open(raw_text_file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    lines = raw_text.split('\n')
    
    # Find table rows (lines with pipe separators and meaningful data)
    data_rows = []
    header_found = False
    
    for i, line in enumerate(lines):
        # Skip until we find the table structure
        if 'Common Stock Outstanding' in line and 'Shareholders' in line:
            header_found = True
            continue
            
        if header_found and '|' in line and ('Balances,' in line or any(keyword in line for keyword in [
            'earnings adjustment', 'comprehensive', 'income', 'stock', 'dividend', 
            'conversion', 'repurchase', 'withholding', 'compensation', 'reclassification'
        ])):
            # This is a data row
            data_rows.append((i + 1, line))
    
    logger.debug_detailed(f"Found {len(data_rows)} data rows to parse")
    
    # Parse each data row
    equity_rows = []
    
    for line_num, line in data_rows:
        # Split by pipe and clean up
        parts = [part.strip() for part in line.split('|')]
        
        # Remove empty parts from start/end
        while parts and not parts[0]:
            parts.pop(0)
        while parts and not parts[-1]:
            parts.pop()
            
        if len(parts) < 8:  # Need at least description + 7 data columns
            logger.debug_detailed(f"Skipping line {line_num}: insufficient columns ({len(parts)})")
            continue
            
        description = parts[0]
        
        # Skip if this doesn't look like a real transaction/balance row
        if not description or len(description) < 5:
            continue
            
        logger.debug_detailed(f"Parsing: {description[:50]}...")
        
        # Map data by exact position (skip position 0 which is description)
        column_values = {}
        
        # Position 1: Shares
        if len(parts) > 1 and parts[1] and parts[1] != '-':
            column_values["Common Stock Outstanding:Shares"] = parts[1]
            
        # Position 2: Amount  
        if len(parts) > 2 and parts[2] and parts[2] != '-':
            column_values["Common Stock Outstanding:Amount"] = parts[2]
            
        # Position 3: Additional Paid-in Capital
        if len(parts) > 3 and parts[3] and parts[3] != '-':
            column_values["Additional Paid-in Capital:"] = parts[3]
            
        # Position 4: Treasury Stock
        if len(parts) > 4 and parts[4] and parts[4] != '-':
            column_values["Treasury Stock:"] = parts[4]
            
        # Position 5: Accumulated Other Comprehensive Income (Loss)
        if len(parts) > 5 and parts[5] and parts[5] != '-':
            column_values["Accumulated Other Comprehensive Income (Loss):"] = parts[5]
            
        # Position 6: Retained Earnings
        if len(parts) > 6 and parts[6] and parts[6] != '-':
            column_values["Retained Earnings:"] = parts[6]
            
        # Position 7: Total Shareholders' Equity (no colon!)
        if len(parts) > 7 and parts[7] and parts[7] != '-':
            column_values["Total Shareholders' Equity"] = parts[7]
        
        # Determine row type and extract date
        row_type = "balance" if "Balances," in description else "transaction"
        date_reference = ""
        
        # Extract date from balance rows
        if row_type == "balance":
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', description)
            if date_match:
                date_reference = date_match.group(0)
        
        row_data = {
            "transaction_description": description,
            "row_type": row_type,
            "date_reference": date_reference,
            "column_values": column_values
        }
        
        equity_rows.append(row_data)
        logger.debug_detailed(f"  ✅ Mapped {len(column_values)} columns")
    
    # Create the complete structure matching the schema
    structured_data = {
        "company_name": "NVIDIA CORPORATION AND SUBSIDIARIES",
        "document_title": "CONSOLIDATED STATEMENTS OF SHAREHOLDERS' EQUITY", 
        "document_type": "shareholders_equity",
        "reporting_periods": [],
        "units_note": "In millions, except per share data",
        "column_headers": [
            {
                "main_header": "Common Stock Outstanding",
                "sub_header": "Shares", 
                "column_index": 1,
                "data_type": "text"
            },
            {
                "main_header": "Common Stock Outstanding",
                "sub_header": "Amount",
                "column_index": 2, 
                "data_type": "currency"
            },
            {
                "main_header": "Additional Paid-in Capital",
                "sub_header": "",
                "column_index": 3,
                "data_type": "currency"
            },
            {
                "main_header": "Treasury Stock", 
                "sub_header": "",
                "column_index": 4,
                "data_type": "currency"
            },
            {
                "main_header": "Accumulated Other Comprehensive Income (Loss)",
                "sub_header": "",
                "column_index": 5,
                "data_type": "currency" 
            },
            {
                "main_header": "Retained Earnings",
                "sub_header": "",
                "column_index": 6,
                "data_type": "currency"
            },
            {
                "main_header": "Total Shareholders' Equity",
                "sub_header": "",
                "column_index": 7,
                "data_type": "currency"
            }
        ],
        "equity_rows": equity_rows,
        "opening_balances": [],
        "closing_balances": [],
        "fiscal_years_covered": []
    }
    
    logger.debug(f"\n🎉 Direct parsing complete!")
    logger.debug(f"📊 Extracted {len(equity_rows)} rows")
    logger.debug(f"📈 Found {len([row for row in equity_rows if row['row_type'] == 'balance'])} balance rows")
    logger.debug(f"📋 Found {len([row for row in equity_rows if row['row_type'] == 'transaction'])} transaction rows")
    
    return structured_data

def save_direct_extraction(structured_data, source_pdf_path):
    """Save the directly parsed data to JSON and Excel."""
    
    # Create output data structure
    output_data = {
        "extraction_method": "direct_raw_text_parsing",
        "document_type": "FinancialStatementType.SHAREHOLDERS_EQUITY", 
        "schema_used": "ShareholdersEquitySchema",
        "detection_confidence": 1.0,
        "source_pdf": source_pdf_path,
        "raw_text_length": 37251,
        "structured_data": json.dumps(structured_data, indent=2),
        "extraction_timestamp": datetime.now().isoformat()
    }
    
    # Save JSON
    pdf_name = Path(source_pdf_path).stem
    json_path = f"output/{pdf_name}_direct_extraction.json"
    
    with open(json_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.debug(f"✅ Direct extraction JSON saved to: {json_path}")
    
    # Save Excel using existing schema system
    excel_path = f"output/{pdf_name}_direct_extraction.xlsx"
    
    try:
        from schemas.excel_exporter import SchemaBasedExcelExporter
        from schemas import schema_registry
        from schemas.base_schema import FinancialStatementType
        
        # Get the schema class
        schema_class = schema_registry.get_schema_class(FinancialStatementType.SHAREHOLDERS_EQUITY)
        schema_instance = schema_class.model_validate(structured_data)
        
        # Create Excel using schema-driven approach
        exporter = SchemaBasedExcelExporter()
        exporter.export_to_excel(schema_instance, excel_path)
        
        logger.debug(f"✅ Direct extraction Excel saved to: {excel_path}")
        
    except Exception as e:
        logger.debug(f"❌ Excel export error: {e}")
        logger.debug("📄 Falling back to basic Excel export...")
        
        # Simple fallback Excel export
        import pandas as pd
        
        # Convert to simple DataFrame structure
        rows_data = []
        for row in structured_data['equity_rows']:
            row_dict = {'Description': row['transaction_description']}
            row_dict.update(row['column_values'])
            rows_data.append(row_dict)
        
        df = pd.DataFrame(rows_data)
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Shareholders Equity', index=False)
        
        logger.debug(f"✅ Fallback Excel saved to: {excel_path}")
    
    return json_path, excel_path

if __name__ == "__main__":
    # Test the direct parser
    raw_text_path = "output/shareholder equity_raw.txt" 
    source_pdf = "input/shareholder equity.pdf"
    
    logger.debug("🚀 Testing Direct Shareholders Equity Parser")
    logger.debug("=" * 60)
    
    structured_data = parse_shareholders_equity_directly(raw_text_path)
    json_path, excel_path = save_direct_extraction(structured_data, source_pdf)
    
    logger.debug(f"\n📄 Files created:")
    logger.debug(f"   JSON: {json_path}")  
    logger.debug(f"   Excel: {excel_path}")