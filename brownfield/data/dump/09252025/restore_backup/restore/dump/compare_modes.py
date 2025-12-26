#!/usr/bin/env python3
"""
Compare LLMWhisperer table vs form mode for shareholder equity
"""

import os
import sys
from dotenv import load_dotenv
from unstract.llmwhisperer import LLMWhispererClientV2
from unstract.llmwhisperer.client_v2 import LLMWhispererClientException

def extract_with_mode(file_path, mode):
    """Extract text using specified mode"""
    print(f"📊 Testing {mode} mode...")
    
    try:
        client = LLMWhispererClientV2()
        result = client.whisper(
            file_path=file_path,
            mode=mode,
            wait_for_completion=True,
            wait_timeout=200
        )
        extracted_text = result["extraction"]["result_text"]
        
        # Save raw text
        raw_path = f"output/raw/shareholder_equity_{mode}_mode.txt"
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(f"# Raw Text Extraction - {mode.upper()} MODE\n")
            f.write(f"# Source PDF: {file_path}\n")
            f.write(f"# Extraction Mode: {mode}\n")
            f.write(f"# Text Length: {len(extracted_text)} characters\n")
            f.write("=" * 80 + "\n\n")
            f.write(extracted_text)
        
        print(f"✅ {mode.upper()} mode saved to: {raw_path}")
        return extracted_text, len(extracted_text)
        
    except LLMWhispererClientException as e:
        print(f"❌ {mode.upper()} mode failed: {e}")
        return None, 0

def main():
    load_dotenv()
    
    pdf_path = "input/shareholder equity.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)
    
    os.makedirs("output/raw", exist_ok=True)
    
    print("🔍 LLMWhisperer Mode Comparison: Table vs Form")
    print("=" * 60)
    
    # Test both modes
    table_text, table_len = extract_with_mode(pdf_path, "table")
    form_text, form_len = extract_with_mode(pdf_path, "form")
    
    print(f"\n📊 COMPARISON RESULTS:")
    print(f"TABLE mode: {table_len:,} characters")
    print(f"FORM mode:  {form_len:,} characters")
    print(f"Difference: {abs(table_len - form_len):,} characters")
    
    if table_text and form_text:
        # Quick structure analysis
        table_lines = table_text.count('\n')
        form_lines = form_text.count('\n')
        
        print(f"\nSTRUCTURE ANALYSIS:")
        print(f"TABLE mode: {table_lines:,} lines")
        print(f"FORM mode:  {form_lines:,} lines")
        
        # Look for table markers
        table_has_pipes = table_text.count('|')
        form_has_pipes = form_text.count('|')
        
        print(f"\nTABLE MARKERS:")
        print(f"TABLE mode: {table_has_pipes:,} pipe characters")
        print(f"FORM mode:  {form_has_pipes:,} pipe characters")

if __name__ == "__main__":
    main()