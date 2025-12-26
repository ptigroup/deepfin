#!/usr/bin/env python3
"""
Test script to run extraction and save raw LLMWhisperer output (validation disabled)
"""

import sys
import os
from financial_table_extractor import FinancialTableExtractor
# BOOKMARKED: Hybrid validation - disabled for raw output analysis
# from hybrid_validator import HybridValidator

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test_hybrid_validation.py <pdf_path>")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print("🚀 Running Financial Extraction Pipeline (Raw Output Mode)")
    print("=" * 70)
    print("📄 NOTE: Validation temporarily disabled to focus on raw LLMWhisperer output")
    
    # Step 1: Extract financial data
    print("\n📊 Step 1: Extracting financial data with LLMWhisperer...")
    extractor = FinancialTableExtractor()
    
    # Get the extracted text directly
    extraction_result = extractor.extract_from_pdf(pdf_path)
    
    if not extraction_result['success']:
        print("❌ Failed to extract data from PDF")
        return
        
    llm_text = extraction_result['text']
    print(f"✅ Extracted {len(llm_text)} characters from PDF")
    
    # Step 2: Generate Excel file
    print("\n📈 Step 2: Generating Excel file...")
    input_name = os.path.splitext(os.path.basename(pdf_path))[0]
    excel_path = f"{input_name}_extracted.xlsx"
    
    success = extractor.process_financial_table(pdf_path, excel_path)
    
    if not success:
        print("❌ Failed to generate Excel file")
        return
    
    print(f"✅ Generated Excel file: {excel_path}")
    
    # BOOKMARKED: Step 3 - Hybrid validation (disabled for raw output analysis)
    """
    print("\n🔍 Step 3: Running hybrid validation...")
    validator = HybridValidator()
    results = validator.validate_extraction(pdf_path, excel_path, llm_text)
    
    print(f"\n🎯 Final Validation Results:")
    print(f"  • Traditional Score: {results['traditional']['score']:.1f}%")
    print(f"  • Semantic Score: {results['semantic']['score']:.1f}%")
    print(f"  • Hybrid Score: {results['hybrid']['final_score']:.1f}% ({results['hybrid']['confidence_level']})")
    """
    
    print("\n🔍 Step 3: Raw output analysis ready")
    print(f"  • Raw text file: {input_name}_raw.txt")
    print(f"  • Excel file: {excel_path}")
    print("\n🕰 Compare these files to identify LLMWhisperer -> Excel conversion issues")

if __name__ == "__main__":
    main()