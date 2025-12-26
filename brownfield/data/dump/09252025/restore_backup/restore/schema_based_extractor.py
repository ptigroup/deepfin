#!/usr/bin/env python3
"""
Schema-Based Financial Extractor using the new modular schema system.

This extractor automatically detects the financial statement type and uses the
appropriate specialized schema for optimal extraction results.

Pipeline: LLMWhisperer → Document Detection → Specialized Schema → ChatOpenAI → Structured JSON → Excel
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
from unstract.llmwhisperer import LLMWhispererClientV2

# Import the new schema system
from schemas import (
    get_schema_for_document,
    schema_registry,
    FinancialStatementType
)

def error_exit(error_message):
    """Exit with error message."""
    print(error_message)
    sys.exit(1)

def check_existing_raw_text(file_path):
    """Check if we have existing raw text extraction for this file."""
    pdf_name = Path(file_path).stem
    raw_path = f"output/raw/{pdf_name}_raw.txt"
    
    if os.path.exists(raw_path):
        print(f"🔄 Found existing raw text extraction: {raw_path}")
        try:
            with open(raw_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip the header metadata
            start_marker = "=" * 80
            start_idx = content.find(start_marker)
            if start_idx != -1:
                extracted_text = content[start_idx + len(start_marker):].strip()
                if extracted_text:
                    print(f"✅ Using existing raw text ({len(extracted_text)} characters)")
                    return extracted_text
        except Exception as e:
            print(f"⚠️ Error reading existing raw text: {e}")
    
    return None

def extract_text_from_pdf(file_path, pages_list=None):
    """Extract text from PDF using LLMWhisperer with smart fallback system."""
    
    # First, check if we have existing raw text
    existing_text = check_existing_raw_text(file_path)
    if existing_text:
        return existing_text
    
    # If no existing text, proceed with LLMWhisperer extraction
    print("🔍 No existing raw text found, performing fresh extraction...")
    
    llmw = LLMWhispererClientV2(
        base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2"
    )
    try:
        result = llmw.whisper(file_path=file_path, pages_to_extract=pages_list)
        
        print(f"🔍 Debug - Result keys: {list(result.keys())}")
        print(f"🔍 Debug - Status code: {result.get('status_code', 'unknown')}")
        
        status_code = result.get('status_code', 0)
        
        if status_code == 200 and "extracted_text" in result:
            # Synchronous success
            return result["extracted_text"]
        elif status_code == 202:
            # Async processing required
            whisper_hash = result.get('whisper_hash', '')
            if whisper_hash:
                print(f"⏳ Document requires async processing (hash: {whisper_hash})")
                
                # Try both full hash and cleaned hash
                full_hash = str(whisper_hash).strip()
                clean_hash = full_hash.split('|')[0].strip() if '|' in full_hash else full_hash
                
                print(f"🔄 Waiting for async processing...")
                extracted_text = wait_for_completion(llmw, clean_hash, full_hash)
                
                if extracted_text:
                    return extracted_text
                else:
                    print("❌ Async processing failed or timed out")
                    # Check one more time for existing raw text (might have been created by another process)
                    fallback_text = check_existing_raw_text(file_path)
                    if fallback_text:
                        return fallback_text
                    error_exit("❌ All extraction methods failed")
            else:
                error_exit("❌ No whisper hash provided for async processing")
        else:
            error_exit(f"❌ Unexpected response format: {result}")
            
    except Exception as e:
        print(f"❌ LLMWhisperer error: {e}")
        # Try fallback to existing raw text one more time
        fallback_text = check_existing_raw_text(file_path)
        if fallback_text:
            print("🔄 Using existing raw text as fallback after API error")
            return fallback_text
        error_exit(f"❌ All extraction methods failed: {e}")

def wait_for_completion(client, clean_hash, full_hash=None, max_retries=5, delay=3):
    """Wait for async processing completion."""
    print(f"🔄 Waiting for async processing (hash: '{clean_hash}')")
    
    # Try different hash formats
    hash_variants = [clean_hash]
    if full_hash and full_hash != clean_hash:
        hash_variants.append(full_hash)
        print(f"🔍 Will also try full hash: '{full_hash}'")
    
    for attempt in range(max_retries):
        print(f"⏳ Attempt {attempt + 1}/{max_retries}: Checking status...")
        
        for hash_variant in hash_variants:
            try:
                print(f"🔍 Trying hash: '{hash_variant}'")
                
                # Try different parameter approaches
                try:
                    status_result = client.whisper_status(whisper_hash=hash_variant)
                except Exception as e1:
                    try:
                        status_result = client.whisper_status(hash_variant)
                    except Exception as e2:
                        print(f"❌ Both parameter methods failed for '{hash_variant}': {e1}")
                        continue
                
                status = status_result.get('status', 'unknown')
                print(f"📊 Status for '{hash_variant}': {status}")
                
                if status == 'processed':
                    print("🎉 Processing completed! Retrieving result...")
                    try:
                        try:
                            retrieve_result = client.whisper_retrieve(whisper_hash=hash_variant)
                        except:
                            retrieve_result = client.whisper_retrieve(hash_variant)
                        
                        extracted_text = retrieve_result.get('extracted_text', '')
                        if extracted_text:
                            print(f"✅ Successfully retrieved {len(extracted_text)} characters")
                            return extracted_text
                    except Exception as e:
                        print(f"❌ Error retrieving result for '{hash_variant}': {e}")
                        continue
                        
                elif status == 'processing':
                    print(f"⏳ Still processing... waiting {delay} seconds")
                    time.sleep(delay)
                    break  # Break inner loop to retry
                else:
                    print(f"❌ Unexpected status '{status}' for hash '{hash_variant}'")
                    continue
                    
            except Exception as e:
                print(f"❌ Error with hash '{hash_variant}': {e}")
                continue
    
    print("❌ Max retries reached with all hash variants")
    return None

def create_specialized_prompt(document_type: FinancialStatementType, extracted_text: str) -> str:
    """Create a specialized prompt based on the detected document type."""
    
    base_preamble = (
        "You are an expert financial statement analyzer. Your job is to accurately extract "
        "structured data from the provided financial statement text. "
    )
    
    type_specific_instructions = {
        FinancialStatementType.INCOME_STATEMENT: (
            "This is an Income Statement. Focus on extracting revenue, expenses, and net income items. "
            "Preserve the account names exactly as they appear and capture all financial values across the reporting periods."
        ),
        
        FinancialStatementType.BALANCE_SHEET: (
            "This is a Balance Sheet. Pay attention to the hierarchical structure of assets, liabilities, and equity. "
            "Capture sub-accounts with their proper indentation levels and ensure totals are properly classified."
        ),
        
        FinancialStatementType.CASH_FLOW: (
            "This is a Cash Flow Statement. Organize the data by activity types: Operating, Investing, and Financing. "
            "Identify subtotals for each activity and maintain the cash flow direction (inflow/outflow)."
        ),
        
        FinancialStatementType.SHAREHOLDERS_EQUITY: (
            "This is a Shareholders' Equity Statement with complex multi-level column headers. "
            "CRITICAL: Extract EVERY single row of data including all individual transactions, not just summary balances. "
            "CRITICAL DATA MAPPING: The table has pipe-separated columns. For each data row, map values BY EXACT POSITION: "
            "Position 0: Transaction Description (ignore for column_values), "
            "Position 1: map to 'Common Stock Outstanding:Shares', "
            "Position 2: map to 'Common Stock Outstanding:Amount', "
            "Position 3: map to 'Additional Paid-in Capital:', "
            "Position 4: map to 'Treasury Stock:', "
            "Position 5: map to 'Accumulated Other Comprehensive Income (Loss):', "
            "Position 6: map to 'Retained Earnings:', "
            "Position 7: map to 'Total Shareholders' Equity' (NO colon). "
            "IGNORE any empty header columns - only use the data positions. Example: if row shows "
            "'| Balances, Jan 26, 2020 | 612 | $ 1 | $ 7,045 | $ (9,814) | $ 1 | $ 14,971 | $ 12,204 |', "
            "then map: Shares=612, Amount=$ 1, Additional=$ 7,045, Treasury=$ (9,814), Accumulated=$ 1, Retained=$ 14,971, Total=$ 12,204. "
            "Extract all transactions including: stock issuances, conversions, repurchases, dividends, adjustments, and all balance rows."
        ),
        
        FinancialStatementType.COMPREHENSIVE_INCOME: (
            "This is a Comprehensive Income Statement. Extract both net income and other comprehensive income items. "
            "Categorize OCI items by type (foreign currency, unrealized gains, etc.) and identify total comprehensive income."
        )
    }
    
    specific_instruction = type_specific_instructions.get(
        document_type, 
        "Extract the financial data maintaining the original structure and formatting."
    )
    
    return base_preamble + specific_instruction

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

def save_raw_text(raw_text, pdf_path):
    """Save raw LLMWhisperer output for debugging."""
    pdf_name = Path(pdf_path).stem
    raw_path = f"output/raw/{pdf_name}_raw.txt"
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    
    with open(raw_path, 'w', encoding='utf-8') as f:
        f.write(f"# Raw LLMWhisperer Output\n")
        f.write(f"# Source PDF: {pdf_path}\n")
        f.write(f"# Extraction Time: {datetime.now().isoformat()}\n")
        f.write(f"# Text Length: {len(raw_text)} characters\n")
        f.write("=" * 80 + "\n\n")
        f.write(raw_text)
    
    print(f"✅ Raw text saved to: {raw_path}")
    return raw_path

def save_detection_details(detection_details, pdf_path):
    """Save document type detection details for analysis."""
    pdf_name = Path(pdf_path).stem
    detection_path = f"output/detection/{pdf_name}_detection.json"
    os.makedirs(os.path.dirname(detection_path), exist_ok=True)
    
    with open(detection_path, 'w') as f:
        json.dump(detection_details, f, indent=2, default=str)
    
    print(f"✅ Detection details saved to: {detection_path}")
    return detection_path

def save_to_json(data, output_path):
    """Save structured data to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ JSON saved to: {output_path}")

def process_with_direct_parsing(raw_text_path, source_pdf_path, schema_class):
    """Process financial statements using direct parsing method."""
    from direct_shareholders_equity_parser import parse_shareholders_equity_directly
    from direct_income_statement_parser import parse_income_statement_directly
    from direct_balance_sheet_parser import parse_balance_sheet_directly
    from direct_comprehensive_income_parser import parse_comprehensive_income_directly
    from schemas.base_schema import FinancialStatementType
    
    print("🎯 Using direct raw text parsing for reliable table structure preservation")
    
    # Determine document type from schema class
    if schema_class.__name__ == "ShareholdersEquitySchema":
        structured_data = parse_shareholders_equity_directly(raw_text_path)
    elif schema_class.__name__ == "IncomeStatementSchema":
        structured_data = parse_income_statement_directly(raw_text_path)
    elif schema_class.__name__ == "BalanceSheetSchema":
        structured_data = parse_balance_sheet_directly(raw_text_path)
    elif schema_class.__name__ == "ComprehensiveIncomeSchema":
        structured_data = parse_comprehensive_income_directly(raw_text_path)
    else:
        raise ValueError(f"Direct parsing not implemented for schema: {schema_class.__name__}")
    
    # Convert to JSON string format that matches LLM output
    import json
    # Handle both Pydantic models and dictionaries
    if hasattr(structured_data, 'model_dump'):
        # Pydantic model
        structured_dict = structured_data.model_dump()
    else:
        # Already a dictionary (legacy shareholders equity parser)
        structured_dict = structured_data
    return json.dumps(structured_dict, indent=2)

def save_to_excel(financial_data, output_path, document_type):
    """Convert structured financial data to Excel using schema-driven approach."""
    from schemas.excel_exporter import SchemaBasedExcelExporter
    from schemas import schema_registry
    
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
            schema_instance = schema_class.model_validate(financial_data)
            
            # Use the schema-based Excel exporter
            exporter = SchemaBasedExcelExporter()
            exporter.export_to_excel(schema_instance, output_path)
        except Exception as e:
            print(f"❌ Error creating schema instance or exporting to Excel: {e}")
            print("📄 Falling back to basic Excel export...")
            
            # Fallback to basic Excel export
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Create simple single-sheet export
                if document_type == FinancialStatementType.SHAREHOLDERS_EQUITY and 'equity_rows' in financial_data:
                    rows_data = []
                    for row in financial_data['equity_rows']:
                        row_data = {'Transaction': row.get('transaction_description', '')}
                        for key, value in row.get('column_values', {}).items():
                            row_data[key] = value
                        rows_data.append(row_data)
                    pd.DataFrame(rows_data).to_excel(writer, index=False)
                else:
                    # Handle other document types
                    line_items = financial_data.get('line_items', financial_data.get('accounts', []))
                    items_data = []
                    for item in line_items:
                        item_data = {'Account Name': item.get('account_name', '')}
                        if 'values' in item:
                            item_data.update(item['values'])
                        items_data.append(item_data)
                    pd.DataFrame(items_data).to_excel(writer, index=False)
            print(f"✅ Basic Excel saved to: {output_path}")
    else:
        print(f"❌ No schema found for document type: {document_type}")

def process_financial_pdf(pdf_path):
    """Process financial PDF using schema-based extraction."""
    load_dotenv()
    
    if not os.path.exists(pdf_path):
        error_exit(f"❌ PDF file not found: {pdf_path}")
    
    pdf_name = Path(pdf_path).stem
    
    print("🚀 Starting Schema-Based Financial Extraction Pipeline")
    print("=" * 60)
    print(f"📄 Input: {pdf_path}")
    
    # Step 1: Extract raw text using LLMWhisperer
    print("\\n📊 Step 1: Extracting raw text with LLMWhisperer...")
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if not extracted_text or not extracted_text.strip():
        error_exit("❌ No text extracted from PDF")
    
    print(f"✅ Extracted {len(extracted_text)} characters of text")
    
    # Step 1.5: Save raw text for debugging
    print("\\n💾 Step 1.5: Saving raw text for debugging...")
    raw_path = save_raw_text(extracted_text, pdf_path)
    
    # Step 2: Detect document type and select schema
    print("\\n🔍 Step 2: Detecting document type and selecting schema...")
    schema_class, document_type, confidence = get_schema_for_document(extracted_text, pdf_name)
    
    # Get detailed detection info
    detection_details = schema_registry.get_detection_details(extracted_text, pdf_name)
    save_detection_details(detection_details, pdf_path)
    
    print(f"✅ Detected document type: {document_type}")
    print(f"📊 Confidence: {confidence:.2f}")
    print(f"🏗️ Using schema: {schema_class.__name__}")
    
    # Step 3: Choose extraction method based on document type
    use_direct_parsing = (document_type in [
        FinancialStatementType.SHAREHOLDERS_EQUITY,
        FinancialStatementType.INCOME_STATEMENT,
        FinancialStatementType.BALANCE_SHEET,
        FinancialStatementType.COMPREHENSIVE_INCOME
    ])
    
    if use_direct_parsing:
        print(f"\\n🎯 Step 3: Using direct parsing for {document_type} (bypassing LLM)...")
        structured_response = process_with_direct_parsing(raw_path, pdf_path, schema_class)
    else:
        # Step 3: Create specialized prompt
        print("\\n📝 Step 3: Creating specialized prompt...")
        specialized_preamble = create_specialized_prompt(document_type, extracted_text)
        
        # Step 4: Convert to structured data using appropriate schema
        print("\\n🤖 Step 4: Converting to structured data with specialized schema...")
        structured_response = compile_template_and_get_llm_response(
            specialized_preamble, 
            extracted_text, 
            schema_class
        )
    
    # Step 5: Save outputs
    print("\\n💾 Step 5: Saving outputs...")
    
    # Save JSON with schema info
    json_path = f"output/structured/json/{pdf_name}_schema_based_extraction.json"
    extraction_method = 'direct_raw_text_parsing' if use_direct_parsing else 'llmwhisperer_schema_based'
    structured_data = {
        'extraction_method': extraction_method,
        'document_type': str(document_type),
        'schema_used': schema_class.__name__,
        'detection_confidence': confidence,
        'source_pdf': pdf_path,
        'raw_text_length': len(extracted_text),
        'structured_data': structured_response,
        'extraction_timestamp': datetime.now().isoformat()
    }
    save_to_json(structured_data, json_path)
    
    # Save Excel with specialized formatting
    excel_path = f"output/structured/excel/{pdf_name}_schema_based_extraction.xlsx"
    save_to_excel(structured_response, excel_path, document_type)  # Pass raw response, let save_to_excel handle parsing
    
    print("\\n🎉 Schema-Based Pipeline completed successfully!")
    print("=" * 60)
    print(f"📊 Document Type: {document_type}")
    print(f"🏗️ Schema: {schema_class.__name__}")
    print(f"📈 Confidence: {confidence:.2f}")
    print(f"📄 JSON: {json_path}")
    print(f"📊 Excel: {excel_path}")
    
    return True

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python3 schema_based_extractor.py <input_pdf_path>")
        print("\\nExample:")
        print('  python3 schema_based_extractor.py "input/shareholder equity.pdf"')
        print("\\nThis extractor will automatically detect the document type and use the appropriate schema.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    process_financial_pdf(pdf_path)

if __name__ == "__main__":
    main()