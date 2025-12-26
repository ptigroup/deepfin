#!/usr/bin/env python3
"""
Test the shareholders equity schema using existing raw text extraction.
This tests if our new specialized schema can properly capture the multi-level headers.
"""

import os
import sys
import json
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

# Import the new schema system
from schemas import (
    get_schema_for_document,
    schema_registry,
    FinancialStatementType
)

def load_raw_text(file_path):
    """Load raw text from existing extraction."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip the header metadata
    start_marker = "=" * 80
    start_idx = content.find(start_marker)
    if start_idx != -1:
        return content[start_idx + len(start_marker):].strip()
    return content

def create_specialized_prompt(document_type: FinancialStatementType) -> str:
    """Create a specialized prompt for shareholders' equity."""
    
    return """You are an expert financial statement analyzer. This is a Shareholders' Equity Statement with complex multi-level column headers.

CRITICAL: Pay special attention to column structure. Main headers like 'Common Stock Outstanding' may span multiple sub-columns like 'Shares' and 'Amount'. Extract the column headers exactly as they appear, including both main headers and sub-headers. Map each data value to the correct main_header:sub_header combination.

The table structure shows:
- Row 1: Main headers (some span multiple columns)
- Row 2: Sub-headers that specify what each column contains (Shares, Amount, etc.)
- Subsequent rows: Transaction data with values for each column

For the column headers, create ShareholdersEquityColumn objects that capture:
- main_header: The main column header (e.g., "Common Stock Outstanding")
- sub_header: The sub-header that explains what this column contains (e.g., "Shares", "Amount")

For each data row, create ShareholdersEquityRow objects with:
- transaction_description: Description of the transaction
- column_values: Dictionary mapping "main_header:sub_header" to the value

Example mapping:
- "Common Stock Outstanding:Shares" -> "585"
- "Common Stock Outstanding:Amount" -> "$ 1"
- "Additional Paid-in Capital:" -> "$ 4,708"
"""

def compile_template_and_get_llm_response(preamble, extracted_text, pydantic_object):
    """Use LangChain + ChatOpenAI to convert text to structured data using specialized schema."""
    postamble = "Do not include any explanation in the reply. Only include the extracted information in the reply."
    system_template = "{preamble}"
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = "{format_instructions}\\n\\n{extracted_text}\\n\\n{postamble}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    parser = PydanticOutputParser(pydantic_object=pydantic_object)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    request = chat_prompt.format_prompt(preamble=preamble,
                                        format_instructions=parser.get_format_instructions(),
                                        extracted_text=extracted_text,
                                        postamble=postamble).to_messages()
    chat = ChatOpenAI(temperature=0.0)
    response = chat(request)
    print(f"Response from LLM:\\n{response.content}")
    return response.content

def save_to_json(data, output_path):
    """Save structured data to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ JSON saved to: {output_path}")

def save_to_excel(financial_data, output_path, document_type):
    """Convert structured financial data to Excel using schema-driven approach."""
    from schemas.excel_exporter import SchemaBasedExcelExporter
    
    # Parse the JSON response
    if isinstance(financial_data, str):
        if financial_data.startswith('```json'):
            start = financial_data.find('{')
            end = financial_data.rfind('}') + 1
            financial_data = json.loads(financial_data[start:end])
        else:
            financial_data = json.loads(financial_data)
    
    # Get the schema class and create instance
    schema_class = schema_registry.get_schema_class(document_type)
    if schema_class:
        try:
            schema_instance = schema_class.parse_obj(financial_data)
            
            # Use the schema-based Excel exporter
            exporter = SchemaBasedExcelExporter()
            exporter.export_to_excel(schema_instance, output_path)
        except Exception as e:
            print(f"❌ Error creating schema instance or exporting to Excel: {e}")
            print("📄 Falling back to basic Excel export...")
            
            # Fallback to basic single-sheet Excel export
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if 'equity_rows' in financial_data:
                    rows_data = []
                    for row in financial_data['equity_rows']:
                        row_data = {'Transaction': row.get('transaction_description', '')}
                        for key, value in row.get('column_values', {}).items():
                            row_data[key] = value
                        rows_data.append(row_data)
                    pd.DataFrame(rows_data).to_excel(writer, index=False)
            print(f"✅ Basic Excel saved to: {output_path}")
    else:
        print(f"❌ No schema found for document type: {document_type}")

def test_shareholders_equity_schema():
    """Test the shareholders equity schema using existing raw text."""
    load_dotenv()
    
    # Load the existing raw text
    raw_text_path = "output/raw/shareholder equity_raw.txt"
    if not os.path.exists(raw_text_path):
        print(f"❌ Raw text file not found: {raw_text_path}")
        sys.exit(1)
    
    print("🚀 Testing Shareholders Equity Schema")
    print("=" * 60)
    print(f"📄 Input: {raw_text_path}")
    
    # Step 1: Load raw text
    print("\\n📊 Step 1: Loading existing raw text...")
    extracted_text = load_raw_text(raw_text_path)
    
    print(f"✅ Loaded {len(extracted_text)} characters of text")
    print(f"📄 Preview: {extracted_text[:300]}...")
    
    # Step 2: Force shareholders equity detection
    print("\\n🔍 Step 2: Using shareholders equity schema...")
    document_type = FinancialStatementType.SHAREHOLDERS_EQUITY
    schema_class = schema_registry.get_schema_class(document_type)
    
    print(f"✅ Using schema: {schema_class.__name__}")
    
    # Step 3: Create specialized prompt
    print("\\n📝 Step 3: Creating specialized prompt...")
    specialized_preamble = create_specialized_prompt(document_type)
    
    # Step 4: Convert to structured data using shareholders equity schema
    print("\\n🤖 Step 4: Converting to structured data with shareholders equity schema...")
    structured_response = compile_template_and_get_llm_response(
        specialized_preamble, 
        extracted_text, 
        schema_class
    )
    
    # Step 5: Save outputs
    print("\\n💾 Step 5: Saving outputs...")
    
    # Save JSON with schema info
    json_path = "output/structured/json/shareholder_equity_schema_test.json"
    structured_data = {
        'extraction_method': 'schema_based_test',
        'document_type': str(document_type),
        'schema_used': schema_class.__name__,
        'source_raw_text': raw_text_path,
        'raw_text_length': len(extracted_text),
        'structured_data': structured_response,
        'extraction_timestamp': datetime.now().isoformat()
    }
    save_to_json(structured_data, json_path)
    
    # Save Excel with specialized formatting
    excel_path = "output/structured/excel/shareholder_equity_schema_test.xlsx"
    save_to_excel(json.loads(structured_response), excel_path, document_type)
    
    print("\\n🎉 Shareholders Equity Schema Test completed successfully!")
    print("=" * 60)
    print(f"📊 Document Type: {document_type}")
    print(f"🏗️ Schema: {schema_class.__name__}")
    print(f"📄 JSON: {json_path}")
    print(f"📊 Excel: {excel_path}")
    
    # Parse and analyze the results
    try:
        parsed_data = json.loads(structured_response)
        print("\\n🔍 Analysis:")
        if 'column_headers' in parsed_data:
            print(f"📋 Column Headers Found: {len(parsed_data['column_headers'])}")
            for i, col in enumerate(parsed_data['column_headers'][:5]):  # Show first 5
                print(f"  {i+1}. {col.get('main_header', '')}: {col.get('sub_header', '')}")
        
        if 'equity_rows' in parsed_data:
            print(f"📊 Data Rows Found: {len(parsed_data['equity_rows'])}")
            
    except Exception as e:
        print(f"⚠️ Could not parse results for analysis: {e}")
    
    return True

if __name__ == "__main__":
    test_shareholders_equity_schema()