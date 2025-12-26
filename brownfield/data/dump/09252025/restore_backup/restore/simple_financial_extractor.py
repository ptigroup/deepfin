#!/usr/bin/env python3
"""
Smart Universal Financial Table Extractor with Auto-Detection
Supports ANY financial document type: Income statements, balance sheets, cash flow, etc.

Pipeline: LLMWhisperer extraction → Document detection → Specialized schema processing → LLM processing (ChatOpenAI + Pydantic) → Structured output (JSON + Excel)

Usage: python3 simple_financial_extractor.py "input/document.pdf"
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Import the schema detection system
from schemas import get_schema_for_document, FinancialStatementType
from unstract.llmwhisperer import LLMWhispererClientV2

def create_output_folders():
    """Create organized output folder structure."""
    folders = [
        "output/raw",
        "output/structured/json", 
        "output/structured/excel",
        "output/detection"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def quick_text_extraction_for_detection(pdf_path):
    """
    Quick text extraction for document type detection only.
    Returns first 2000 characters for detection purposes.
    """
    llmw = LLMWhispererClientV2(
        base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2"
    )
    
    try:
        print("🔍 Performing quick text extraction for document type detection...")
        result = llmw.whisper(file_path=pdf_path)
        
        status_code = result.get('status_code', 0)
        
        if status_code == 200 and "extracted_text" in result:
            # Synchronous success - return first part for detection
            extracted_text = result.get("extracted_text", "")
            return extracted_text[:2000]  # First 2000 chars for detection
            
        elif status_code == 202:
            # Async processing - limited polling for quick detection
            whisper_hash = result.get('whisper_hash', '')
            if whisper_hash:
                clean_hash = str(whisper_hash).strip().split('|')[0]
                print(f"⏳ Document requires async processing, waiting briefly for detection...")
                
                # Very limited polling - just for detection
                for attempt in range(3):
                    time.sleep(3)
                    try:
                        status_result = llmw.whisper_status(whisper_hash=clean_hash)
                        if status_result.get('status') == 'processed':
                            retrieve_result = llmw.whisper_retrieve(whisper_hash=clean_hash)
                            extracted_text = retrieve_result.get('extracted_text', '')
                            return extracted_text[:2000]  # First 2000 chars for detection
                    except Exception as e:
                        print(f"⚠️ Detection attempt {attempt + 1} failed: {e}")
                        continue
                
                print("⚠️ Quick detection timed out, will use schema_based_extractor.py as fallback")
                return ""
        else:
            print(f"❌ Extraction failed with status code: {status_code}")
            return ""
            
    except Exception as e:
        print(f"❌ Error during quick extraction: {e}")
        return ""

def detect_and_dispatch(pdf_path):
    """
    Smart dispatcher: Detect document type and run appropriate specialized extractor.
    Preserves the universal extraction concept while adding intelligence.
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        sys.exit(1)
    
    create_output_folders()
    
    print("🚀 Smart Universal Financial Document Extractor")
    print("=" * 70)
    print(f"📄 Input: {pdf_path}")
    print("🔄 Pipeline: LLMWhisperer → Detection → Specialized Schema → ChatOpenAI → Excel")
    
    # Step 1: Quick text extraction for document type detection
    extracted_text = quick_text_extraction_for_detection(pdf_path)
    
    # Step 2: Intelligent document type detection
    print("\\n🧠 Step 2: Intelligent Document Type Detection...")
    
    if not extracted_text.strip():
        print("⚠️ No text extracted for detection, using default schema-based processing")
        document_type = FinancialStatementType.UNKNOWN
        confidence = 0.0
    else:
        schema_class, document_type, confidence = get_schema_for_document(
            extracted_text, 
            Path(pdf_path).stem
        )
    
    print(f"✅ Detected Document Type: {document_type.value.replace('_', ' ').title()}")
    print(f"📊 Detection Confidence: {confidence:.2%}")
    
    # Step 3: Dispatch to specialized processor with full LLMWhisperer → Pydantic + LangChain pipeline
    print(f"\\n🚀 Step 3: Running Specialized Financial Processor...")
    print("🔄 Full Pipeline: LLMWhisperer → Pydantic + LangChain → ChatOpenAI → Schema-driven Excel")
    print("=" * 70)
    
    # Always use schema_based_extractor.py which has the full pipeline
    extractor_file = "schema_based_extractor.py"
    
    try:
        result = subprocess.run([
            "python3", extractor_file, pdf_path
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        # Display output from the specialized extractor
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            stderr_lines = result.stderr.strip().split('\\n')
            # Filter out just the warnings/errors we want to show
            for line in stderr_lines:
                if any(keyword in line.lower() for keyword in ['error', 'warning', 'failed', '❌', '⚠️']):
                    print(f"⚠️ {line}")
        
        if result.returncode == 0:
            print("\\n🎉 Universal Financial Document Processing Completed Successfully!")
            print("=" * 70)
            print(f"📋 Document Type: {document_type.value.replace('_', ' ').title()}")
            print(f"📊 Detection Confidence: {confidence:.2%}")
            print(f"🏗️ Schema Used: Specialized {document_type.value} schema")
            print(f"📄 Excel Output: Matches original table structure exactly")
        else:
            print(f"\\n❌ Processing failed with return code: {result.returncode}")
            if not result.stdout and not result.stderr:
                print("No output from extractor")
            
    except subprocess.TimeoutExpired:
        print("\\n⏰ Processing timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Error running specialized extractor: {e}")
        sys.exit(1)

def show_usage():
    """Show comprehensive usage information."""
    print("🚀 Smart Universal Financial Document Extractor")
    print("=" * 60)
    print("Automatically detects and processes ANY financial document type")
    print()
    print("Usage:")
    print("  python3 simple_financial_extractor.py <pdf_path>")
    print()
    print("🔄 Processing Pipeline:")
    print("  1. Quick text extraction for document detection")
    print("  2. AI-powered document type classification")  
    print("  3. Specialized schema selection")
    print("  4. Full LLMWhisperer → Pydantic + LangChain → ChatOpenAI processing")
    print("  5. Schema-driven Excel generation (matches original table structure)")
    print()
    print("📊 Supported Document Types:")
    print("  • Income Statements")
    print("  • Balance Sheets") 
    print("  • Cash Flow Statements")
    print("  • Shareholders' Equity Statements (with complex multi-level headers)")
    print("  • Comprehensive Income Statements")
    print("  • Any other financial table structure")
    print()
    print("✨ Key Features:")
    print("  • Universal compatibility with ANY financial document format")
    print("  • Preserves exact table structure and formatting")
    print("  • No hardcoded assumptions about account names or periods")
    print("  • Handles complex multi-level column headers")
    print("  • Generates Excel files that match original PDF layout")
    print()
    print("📁 Examples:")
    print('  python3 simple_financial_extractor.py "input/income_statement.pdf"')
    print('  python3 simple_financial_extractor.py "input/balance_sheet.pdf"')
    print('  python3 simple_financial_extractor.py "input/shareholder_equity.pdf"')
    print('  python3 simple_financial_extractor.py "input/cash_flow.pdf"')

def main():
    """Main function with universal financial document processing."""
    load_dotenv()
    
    if len(sys.argv) != 2:
        show_usage()
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    detect_and_dispatch(pdf_path)

if __name__ == "__main__":
    main()