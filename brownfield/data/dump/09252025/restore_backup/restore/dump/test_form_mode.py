#!/usr/bin/env python3
"""
Test form mode extraction for shareholder equity
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from unstract.llmwhisperer import LLMWhispererClientV2
from unstract.llmwhisperer.client_v2 import LLMWhispererClientException
from pydantic import BaseModel, Field
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser

# Same schemas as the main extractor
class UniversalFinancialLineItem(BaseModel):
    account_name: str = Field(description="Exact account name as it appears, preserving all spacing and punctuation")
    indent_level: int = Field(description="Indentation level: 0=main item, 1=sub-item, 2=sub-sub-item, etc.")
    is_section_header: bool = Field(description="True if this line is a section header (ends with ':' and has no values)")
    parent_section: str = Field(description="Name of parent section if this is a sub-item, empty string if top-level", default="")
    values: dict = Field(description="Dictionary mapping period names to values. Empty dict for section headers")

class UniversalFinancialStatement(BaseModel):
    company_name: str = Field(description="Name of the company or entity")
    document_title: str = Field(description="Title of the financial document")
    document_type: str = Field(description="Type of financial document (income statement, balance sheet, cash flow, etc.)")
    units_note: str = Field(description="Units specification from document (e.g., 'In millions', 'In thousands, except per share data')", default="")
    reporting_periods: list[str] = Field(description="List of reporting periods exactly as they appear in the document")
    line_items: list[UniversalFinancialLineItem] = Field(description="List of all line items preserving exact hierarchical structure")

def extract_text_from_pdf_form_mode(file_path):
    """Extract text using form mode"""
    pdf_name = Path(file_path).stem
    
    print(f"📄 Extracting text from: {file_path} (FORM MODE)")
    
    try:
        client = LLMWhispererClientV2()
        result = client.whisper(
            file_path=file_path,
            mode="form",  # Use form mode
            wait_for_completion=True,
            wait_timeout=200
        )
        extracted_text = result["extraction"]["result_text"]
        
        # Save raw text
        raw_path = f"output/raw/{pdf_name}_form_mode_test.txt"
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(f"# Raw Text Extraction - FORM MODE TEST\n")
            f.write(f"# Source PDF: {file_path}\n")
            f.write(f"# Extraction Method: LLMWhisperer API (form mode)\n")
            f.write(f"# Extraction Time: {datetime.now().isoformat()}\n")
            f.write(f"# Text Length: {len(extracted_text)} characters\n")
            f.write("=" * 80 + "\n\n")
            f.write(extracted_text)
        
        print(f"✅ Raw text saved to: {raw_path}")
        return extracted_text
        
    except LLMWhispererClientException as e:
        print(f"❌ LLMWhisperer extraction failed: {e}")
        return None

def compile_template_and_get_llm_response(preamble, extracted_text, pydantic_object):
    """Same LLM processing as main extractor"""
    postamble = "Do not include any explanation in the reply. Only include the extracted information in the reply."
    system_template = "{preamble}"
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_template = "{format_instructions}\n\n{extracted_text}\n\n{postamble}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    parser = PydanticOutputParser(pydantic_object=pydantic_object)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    request = chat_prompt.format_prompt(preamble=preamble,
                                        format_instructions=parser.get_format_instructions(),
                                        extracted_text=extracted_text,
                                        postamble=postamble).to_messages()
    chat = ChatOpenAI(temperature=0.0)
    response = chat(request)
    print(f"✅ LLM Response received: {response.content[:200]}...")
    return response.content

def extract_financial_data_from_text(extracted_text):
    """Same prompt as main extractor"""
    preamble = ("You are extracting data from a financial document. Focus on STRUCTURE PATTERNS, not content meaning. "
                "UNIVERSAL RULES (work for any financial document type): "
                "1. MULTI-ROW HEADERS: When table headers span multiple rows, combine them properly "
                "   - Example: Row 1 'Year Ended' + Row 2 'January 26, 2020' = 'Year Ended January 26, 2020' "
                "   - Do NOT treat header fragments as separate periods "
                "2. COMPLEX TABLE STRUCTURES: Handle multi-column layouts like shareholders' equity "
                "   - For equity statements: Rows are transactions/changes, columns are account types "
                "   - Transaction rows like 'Net income', 'Share repurchase' are account_name entries "
                "   - Column headers like 'Common Stock', 'Retained Earnings' become period names "
                "   - Extract ALL data rows, not just headers "
                "3. DISCLOSURE LINES: Always preserve reference lines even without numerical values "
                "   - Patterns: Any line containing 'Note [number]', 'see Note', 'contingencies', 'commitments' "
                "   - Examples: 'Commitments and contingencies - see Note 13', 'See accompanying notes' "
                "   - Set is_section_header=false, values={} but MUST be included in line_items "
                "4. INDENTATION LEVELS: Count leading spaces to determine hierarchy (0=main, 1=sub-item, 2=sub-sub-item) "
                "5. SECTION HEADERS: Lines ending with ':' that have NO numerical values are section headers "
                "6. EXACT TEXT: Preserve account names exactly - never modify, combine, or interpret "
                "7. PERIOD MAPPING: Use exact period headers from the table, map values to corresponding periods "
                "8. HIERARCHY PRESERVATION: "
                "   - Section header 'Operating expenses:' → is_section_header=true, values={} "
                "   - Sub-item '     Research and development' → indent_level=1, parent_section='Operating expenses' "
                "   - Main item 'Revenue' → indent_level=0, is_section_header=false "
                "9. UNITS DETECTION: Look for parenthetical text near document title containing unit specifications "
                "   - Examples: '(In millions)', '(In thousands)', '(In millions, except per share data)' "
                "   - Extract EXACT text including parentheses - preserve all unit specifications "
                "   - If no units found, set units_note to empty string "
                "10. UNIVERSAL APPROACH: This works for income statements, balance sheets, cash flow, equity - ANY financial table "
                "11. PATTERN DETECTION: Focus on structure and layout, adapt to different document formats")
    
    return compile_template_and_get_llm_response(preamble, extracted_text, UniversalFinancialStatement)

def save_structured_outputs(structured_response, pdf_path, mode_suffix=""):
    """Save outputs with mode suffix"""
    pdf_name = Path(pdf_path).stem
    
    # Save JSON
    json_data = {
        'extraction_method': f'llmwhisperer_pydantic_langchain_{mode_suffix}',
        'source_pdf': pdf_path,
        'structured_data': structured_response,
        'extraction_timestamp': datetime.now().isoformat()
    }
    
    json_path = f"output/structured/json/{pdf_name}_{mode_suffix}_extraction.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"✅ JSON saved to: {json_path}")
    
    # Parse and save Excel
    try:
        if structured_response.startswith('```json'):
            start = structured_response.find('{')
            end = structured_response.rfind('}') + 1
            financial_data = json.loads(structured_response[start:end])
        else:
            financial_data = json.loads(structured_response)
        
        line_items = financial_data.get('line_items', [])
        reporting_periods = financial_data.get('reporting_periods', [])
        
        df_data = []
        for item in line_items:
            row = []
            values = item.get('values', {})
            indent_level = item.get('indent_level', 0)
            
            indent_prefix = "    " * indent_level
            account_display = indent_prefix + item['account_name']
            row.append(account_display)
            
            for period in reporting_periods:
                row.append(values.get(period, ''))
            
            df_data.append(row)
        
        # Handle duplicate column names
        columns = ['']
        seen_columns = set()
        for period in reporting_periods:
            original_period = period
            counter = 1
            while period in seen_columns:
                period = f"{original_period}_{counter}"
                counter += 1
            seen_columns.add(period)
            columns.append(period)
        
        df = pd.DataFrame(df_data, columns=columns)
        
        # Add units info
        units_info = financial_data.get('units_note', '')
        excel_path = f"output/structured/excel/{pdf_name}_{mode_suffix}_extraction.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            if units_info:
                separator_row = pd.DataFrame({
                    '': [''],
                    **{period: [''] for period in reporting_periods}
                })
                units_notice = pd.DataFrame({
                    '': [f'📊 UNITS: {units_info}'],
                    **{period: [''] for period in reporting_periods}
                })
                combined_df = pd.concat([df, separator_row, units_notice], ignore_index=True)
                combined_df.to_excel(writer, sheet_name='Financial Data', index=False)
            else:
                df.to_excel(writer, sheet_name='Financial Data', index=False)
        
        print(f"✅ Excel saved to: {excel_path}")
        print(f"📊 Document type: {financial_data.get('document_type', 'Unknown')}")
        print(f"📊 Extracted {len(df)} financial line items")
        return True
        
    except Exception as e:
        print(f"❌ Error saving Excel: {e}")
        return False

def main():
    load_dotenv()
    
    pdf_path = "input/shareholder equity.pdf"
    
    os.makedirs("output/raw", exist_ok=True)
    os.makedirs("output/structured/json", exist_ok=True)
    os.makedirs("output/structured/excel", exist_ok=True)
    
    print("🔍 Testing FORM MODE for Shareholder Equity")
    print("=" * 60)
    
    # Extract with form mode
    raw_text = extract_text_from_pdf_form_mode(pdf_path)
    
    if raw_text:
        # Process with LLM
        print("\n🤖 LLM processing...")
        structured_response = extract_financial_data_from_text(raw_text)
        
        # Save outputs
        print("\n💾 Saving outputs...")
        success = save_structured_outputs(structured_response, pdf_path, "form_mode")
        
        if success:
            print("\n🎉 Form mode test completed successfully!")
        else:
            print("\n❌ Form mode test completed with errors")

if __name__ == "__main__":
    main()