#!/usr/bin/env python3
"""
Proper Financial Table Extractor using the official LLMWhisperer methodology
Based on llmwhisperer-table-extraction-main/main.py

Pipeline: LLMWhisperer → Raw Text → Pydantic + LangChain → ChatOpenAI → Structured JSON → Excel
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from unstract.llmwhisperer import LLMWhispererClient

# Define Pydantic schema for financial statements (like official example)
class FinancialLineItem(BaseModel):
    account_name: str = Field(description="Name of the financial account/line item")
    current_period: str = Field(description="Value for the most recent period")
    previous_period: str = Field(description="Value for the previous period", default="")
    third_period: str = Field(description="Value for the third period if available", default="")

class FinancialStatement(BaseModel):
    company_name: str = Field(description="Name of the company")
    document_title: str = Field(description="Title of the financial statement")
    reporting_periods: list[str] = Field(description="List of reporting periods (years/quarters)")
    line_items: list[FinancialLineItem] = Field(description="List of financial line items with their values")

def error_exit(error_message):
    """Exit with error message."""
    print(error_message)
    sys.exit(1)

def extract_text_from_pdf(file_path, pages_list=None):
    """Extract text from PDF using LLMWhisperer (from official example)."""
    # Use v2 endpoint like our working clients
    llmw = LLMWhispererClient(
        base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2"
    )
    try:
        result = llmw.whisper(file_path=file_path, pages_to_extract=pages_list)
        
        # Debug: Check what we got
        print(f"🔍 Debug - Result keys: {list(result.keys())}")
        print(f"🔍 Debug - Status code: {result.get('status_code', 'unknown')}")
        
        # Handle different response types
        if "extracted_text" in result:
            # Synchronous response
            return result["extracted_text"]
        elif result.get('status_code') == 202:
            # Async response - for now, return error asking to use other extractor
            error_exit(f"❌ PDF requires async processing. Please use financial_table_extractor.py instead.")
        else:
            error_exit(f"❌ Unexpected response format: {result}")
            
    except Exception as e:
        error_exit(f"LLMWhisperer error: {e}")

def compile_template_and_get_llm_response(preamble, extracted_text, pydantic_object):
    """Use LangChain + ChatOpenAI to convert text to structured data (from official example)."""
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
    chat = ChatOpenAI()
    response = chat(request, temperature=0.0)
    print(f"Response from LLM:\\n{response.content}")
    return response.content

def extract_financial_statement_from_text(extracted_text):
    """Extract financial statement using proper methodology."""
    preamble = ("You're seeing a financial statement (income statement, balance sheet, etc.) and your job is to accurately "
                "extract the company name, document title, reporting periods, and all financial line items with their values "
                "across the different time periods shown.")
    return compile_template_and_get_llm_response(preamble, extracted_text, FinancialStatement)

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

def save_to_json(data, output_path):
    """Save structured data to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON saved to: {output_path}")

def save_to_excel(financial_data, output_path):
    """Convert structured financial data to Excel."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Parse the JSON response
    if isinstance(financial_data, str):
        # Remove markdown code blocks if present
        if financial_data.startswith('```json'):
            start = financial_data.find('{')
            end = financial_data.rfind('}') + 1
            financial_data = json.loads(financial_data[start:end])
        else:
            financial_data = json.loads(financial_data)
    
    # Convert line items to DataFrame
    df = pd.DataFrame([item.__dict__ if hasattr(item, '__dict__') else item for item in financial_data['line_items']])
    
    # Create metadata
    metadata = {
        'Company Name': [financial_data.get('company_name', 'Unknown')],
        'Document Title': [financial_data.get('document_title', 'Unknown')], 
        'Reporting Periods': [', '.join(financial_data.get('reporting_periods', []))],
        'Extraction Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    }
    metadata_df = pd.DataFrame(metadata)
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Financial Data', index=False)
        metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    print(f"✅ Excel saved to: {output_path}")
    return df

def process_financial_pdf(pdf_path):
    """Process financial PDF using proper LLMWhisperer → Pydantic + LangChain methodology."""
    load_dotenv()
    
    if not os.path.exists(pdf_path):
        error_exit(f"❌ PDF file not found: {pdf_path}")
    
    pdf_name = Path(pdf_path).stem
    
    print("🚀 Starting Proper Financial Extraction Pipeline")
    print("=" * 60)
    print(f"📄 Input: {pdf_path}")
    
    # Step 1: Extract raw text using LLMWhisperer
    print("\\n📊 Step 1: Extracting raw text with LLMWhisperer...")
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if not extracted_text or not extracted_text.strip():
        error_exit("❌ No text extracted from PDF")
    
    print(f"✅ Extracted {len(extracted_text)} characters of text")
    print(f"📄 Preview: {extracted_text[:200]}...")
    
    # Step 1.5: Save raw text for debugging
    print("\\n💾 Step 1.5: Saving raw text for debugging...")
    raw_path = save_raw_text(extracted_text, pdf_path)
    
    # Step 2: Convert to structured data using Pydantic + LangChain  
    print("\\n🤖 Step 2: Converting to structured data with ChatOpenAI...")
    structured_response = extract_financial_statement_from_text(extracted_text)
    
    # Step 3: Save outputs
    print("\\n💾 Step 3: Saving outputs...")
    
    # Save JSON
    json_path = f"output/structured/json/{pdf_name}_proper_extraction.json"
    structured_data = {
        'extraction_method': 'llmwhisperer_pydantic_langchain',
        'source_pdf': pdf_path,
        'raw_text_length': len(extracted_text),
        'structured_data': structured_response,
        'extraction_timestamp': datetime.now().isoformat()
    }
    save_to_json(structured_data, json_path)
    
    # Save Excel 
    excel_path = f"output/structured/excel/{pdf_name}_proper_extraction.xlsx"
    df = save_to_excel(json.loads(structured_response), excel_path)
    
    print("\\n🎉 Pipeline completed successfully!")
    print("=" * 60)
    print(f"📊 Extracted {len(df)} financial line items")
    print(f"📄 JSON: {json_path}")
    print(f"📊 Excel: {excel_path}")
    
    return True

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python3 proper_financial_extractor.py <input_pdf_path>")
        print("\\nExample:")
        print('  python3 proper_financial_extractor.py "input/income statement.pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    process_financial_pdf(pdf_path)

if __name__ == "__main__":
    main()