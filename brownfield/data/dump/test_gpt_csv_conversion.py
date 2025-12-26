#!/usr/bin/env python3
"""
Test GPT-4o-mini CSV conversion from LLMWhisperer raw text
"""

import os
import openai
import pandas as pd
from dotenv import load_dotenv

def convert_raw_text_to_csv_with_gpt(raw_text_file):
    """
    Use GPT-4o-mini to convert LLMWhisperer raw text directly to CSV format.
    
    Args:
        raw_text_file (str): Path to raw LLMWhisperer text file
        
    Returns:
        str: CSV formatted text from GPT
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print(f"📄 Reading raw text from: {raw_text_file}")
    
    # Read the raw text file
    with open(raw_text_file, 'r', encoding='utf-8') as f:
        raw_content = f.read()
    
    # Remove the metadata header (everything before the ===== line)
    if '=' * 80 in raw_content:
        raw_content = raw_content.split('=' * 80, 1)[1].strip()
    
    print(f"📝 Raw content length: {len(raw_content)} characters")
    print(f"📄 First 300 chars: {repr(raw_content[:300])}")
    print("-" * 60)
    
    # Create prompt for GPT-4o-mini
    prompt = f"""Convert this financial statement text to CSV format. 

Requirements:
- First row should be column headers
- Account names in first column (ALWAYS quote account names with commas)
- Numerical values in subsequent columns
- Preserve all numbers exactly as shown
- Handle negative numbers (parentheses) as negative values
- Skip non-data rows like "Table of Contents"
- Include proper headers like: Account,2020,2019,2018
- Quote any field containing commas (e.g., "Sales, general and administrative")

Financial statement text:
{raw_content}

Output only the CSV data, no explanation:"""

    print("🤖 Sending to GPT-4o-mini for CSV conversion...")
    
    try:
        # Call GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at converting financial statement text to CSV format. Output only clean CSV data with no additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # For consistent results
            max_tokens=2000
        )
        
        csv_content = response.choices[0].message.content.strip()
        print("✅ GPT-4o-mini conversion completed!")
        print(f"📊 CSV output length: {len(csv_content)} characters")
        print("-" * 60)
        print("📄 GPT CSV Output:")
        print(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)
        
        return csv_content
        
    except Exception as e:
        print(f"❌ Error calling GPT-4o-mini: {e}")
        return None

def save_and_test_csv(csv_content, output_file):
    """
    Save CSV content and test by loading into pandas.
    """
    if not csv_content:
        print("❌ No CSV content to save")
        return False
    
    # Save CSV content to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    
    print(f"💾 Saved CSV to: {output_file}")
    
    # Test loading with pandas
    try:
        df = pd.read_csv(output_file)
        print(f"✅ Successfully loaded CSV into pandas!")
        print(f"📊 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"📋 Columns: {list(df.columns)}")
        print("\n📄 First 10 rows:")
        print(df.head(10).to_string(index=False))
        return True
        
    except Exception as e:
        print(f"❌ Error loading CSV with pandas: {e}")
        return False

def main():
    """Test the GPT-4o-mini CSV conversion approach."""
    raw_file = "income statement_raw.txt"
    csv_file = "income_statement_gpt_converted.csv"
    
    if not os.path.exists(raw_file):
        print(f"❌ Raw file not found: {raw_file}")
        print("Run: python3 financial_table_extractor.py \"input/income statement.pdf\" first")
        return
    
    print("🚀 Testing GPT-4o-mini CSV Conversion")
    print("=" * 60)
    
    # Step 1: Convert raw text to CSV using GPT
    csv_content = convert_raw_text_to_csv_with_gpt(raw_file)
    
    if csv_content:
        # Step 2: Save and test the CSV
        success = save_and_test_csv(csv_content, csv_file)
        
        if success:
            print("\n🎯 GPT-4o-mini CSV conversion test: SUCCESS!")
            print(f"📊 Compare this with current broken Excel output")
        else:
            print("\n❌ CSV conversion test failed")
    else:
        print("\n❌ GPT conversion failed")

if __name__ == "__main__":
    main()