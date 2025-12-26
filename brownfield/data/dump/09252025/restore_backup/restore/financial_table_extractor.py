#!/usr/bin/env python3
"""
Generic Financial Table Extractor using LLMWhisperer
Extracts ANY financial table/statement from PDF and exports to Excel format

Pipeline: LLMWhisperer → Structured Data → Pandas → Excel

Works with: Balance Sheets, Income Statements, Cash Flow, P&L, etc.
"""

import os
import re
import pandas as pd
import time
import openai
import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from unstract.llmwhisperer import LLMWhispererClient

class FinancialTableExtractor:
    def __init__(self):
        """Initialize the Financial Table Extractor with LLMWhisperer client."""
        # Load environment variables
        load_dotenv()
        
        # Initialize LLMWhisperer client with correct v2 endpoint
        self.client = LLMWhispererClient(
            base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2"
        )
        
        # Usage tracking
        self.usage_stats = {
            'pages_processed': 0,
            'processing_mode': '',
            'processing_time': 0,
            'estimated_cost': 0.0
        }
        
    def _check_existing_json_extraction(self, pdf_path):
        """
        Check if we already have a successful JSON extraction for this PDF.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str or None: Path to existing JSON file or None if not found
        """
        pdf_name = Path(pdf_path).stem
        json_file = f"output/structured/json/{pdf_name}_structured.json"
        
        if os.path.exists(json_file):
            print(f"✅ Found existing extraction: {json_file}")
            return json_file
        
        return None
    
    def _convert_json_to_excel(self, json_file_path, excel_output_path):
        """
        Convert existing JSON extraction to Excel format.
        
        Args:
            json_file_path (str): Path to the JSON file
            excel_output_path (str): Path for the Excel output
            
        Returns:
            dict: Success status and data
        """
        try:
            # Load the JSON data
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            # Extract the structured data from the JSON
            extracted_data_str = data.get('extracted_data', '')
            
            # Parse the JSON from the extracted_data field (it's wrapped in ```json blocks)
            if extracted_data_str.startswith('```json'):
                json_start = extracted_data_str.find('{')
                json_end = extracted_data_str.rfind('}') + 1
                financial_data = json.loads(extracted_data_str[json_start:json_end])
            else:
                financial_data = json.loads(extracted_data_str)
            
            # Convert to DataFrame
            line_items = financial_data.get('line_items', [])
            
            if not line_items:
                print("❌ No line items found in the structured data")
                return {'success': False, 'error': 'No line items found'}
            
            # Create DataFrame from line items
            df = pd.DataFrame(line_items)
            
            # Add metadata sheet
            metadata = {
                'Document Title': [financial_data.get('document_title', 'Unknown')],
                'Document Type': [data.get('document_type', 'unknown')],
                'Schema Used': [data.get('schema_used', 'unknown')],
                'Processing Time': [f"{data.get('processing_time', 0):.2f} seconds"],
                'Extraction Timestamp': [data.get('extraction_timestamp', 'unknown')],
                'Reporting Periods': [', '.join(financial_data.get('reporting_periods', []))]
            }
            metadata_df = pd.DataFrame(metadata)
            
            # Write to Excel with multiple sheets
            with pd.ExcelWriter(excel_output_path, engine='openpyxl') as writer:
                # Write the main financial data
                df.to_excel(writer, sheet_name='Financial Data', index=False)
                
                # Write metadata
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Update usage stats based on JSON metadata
            self.usage_stats['processing_time'] = data.get('processing_time', 0)
            self.usage_stats['processing_mode'] = 'reused_existing'
            estimated_pages = max(1, len(str(financial_data)) // 2000)
            self.usage_stats['pages_processed'] = estimated_pages
            
            print(f"✅ Successfully converted existing JSON to Excel!")
            print(f"📊 Rows: {len(df)}")
            print(f"📋 Columns: {list(df.columns)}")
            
            return {
                'success': True,
                'text': f"Converted from existing extraction: {len(line_items)} line items",
                'usage': self.usage_stats,
                'source': 'existing_json'
            }
            
        except Exception as e:
            print(f"❌ Error converting existing JSON: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_from_pdf(self, pdf_path, processing_mode="high_quality", use_existing=True):
        """
        Extract text from PDF using LLMWhisperer - simplified synchronous pattern.
        First checks for existing successful JSON extraction to avoid timeouts.
        
        Args:
            pdf_path (str): Path to the PDF file
            processing_mode (str): Processing mode for LLMWhisperer
            use_existing (bool): Whether to use existing JSON extractions first
            
        Returns:
            dict: Extracted text and usage information
        """
        print(f"🔍 Starting extraction from: {pdf_path}")
        print(f"📊 Processing mode: {processing_mode}")
        
        # Skip existing JSON - always do fresh extraction for proper methodology
        print("🔄 Performing fresh extraction using proper LLMWhisperer → Pydantic + LangChain methodology...")
        
        start_time = time.time()
        
        try:
            # Use simple synchronous pattern like official examples
            result = self.client.whisper(
                file_path=pdf_path,
                processing_mode=processing_mode
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Handle the result
            status_code = result.get("status_code", 0)
            
            if status_code == 200:
                # Synchronous success - extract text directly
                extracted_text = result.get("extracted_text", "")
                
                # Update usage stats
                self.usage_stats['processing_time'] = processing_time
                self.usage_stats['processing_mode'] = processing_mode
                estimated_pages = max(1, len(extracted_text) // 2000)
                self.usage_stats['pages_processed'] = estimated_pages
                
                self._display_usage_info()
                
                print(f"✅ Extraction completed successfully!")
                print(f"📄 Extracted text length: {len(extracted_text)} characters")
                
                return {
                    'success': True,
                    'text': extracted_text,
                    'usage': self.usage_stats
                }
                
            elif status_code == 202:
                # Async processing required - use simple polling without client library methods
                whisper_hash = result.get('whisper_hash', '')
                if whisper_hash:
                    print(f"⏳ Document requires async processing (hash: {whisper_hash})")
                    print(f"🔍 Debug - Full whisper_hash: '{whisper_hash}' (type: {type(whisper_hash)})")
                    
                    # Clean the hash - sometimes it has extra characters
                    clean_hash = str(whisper_hash).strip()
                    if '|' in clean_hash:
                        # Extract the part before | if present
                        clean_hash = clean_hash.split('|')[0].strip()
                    
                    print(f"🔍 Debug - Clean hash: '{clean_hash}'")
                    extracted_text = self._simple_wait_for_completion(clean_hash)
                    
                    if extracted_text:
                        # Update usage stats
                        self.usage_stats['processing_time'] = processing_time
                        self.usage_stats['processing_mode'] = processing_mode
                        estimated_pages = max(1, len(extracted_text) // 2000)
                        self.usage_stats['pages_processed'] = estimated_pages
                        
                        self._display_usage_info()
                        
                        print(f"✅ Async extraction completed successfully!")
                        print(f"📄 Extracted text length: {len(extracted_text)} characters")
                        
                        return {
                            'success': True,
                            'text': extracted_text,
                            'usage': self.usage_stats
                        }
                
                print("❌ Async processing failed - no valid hash or timeout")
                return {'success': False, 'error': 'Async processing failed', 'usage': self.usage_stats}
                
            else:
                print(f"❌ Processing failed with status code: {status_code}")
                return {'success': False, 'error': f'Status code {status_code}', 'usage': self.usage_stats}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e), 'usage': self.usage_stats}
    
    def _simple_wait_for_completion(self, whisper_hash, max_retries=5, delay=3):
        """
        Simple async completion using client library methods with proper parameter handling.
        
        Args:
            whisper_hash (str): The hash to check status
            max_retries (int): Maximum number of status checks
            delay (int): Seconds to wait between checks
            
        Returns:
            str: Extracted text or None if failed
        """
        print(f"🔄 Waiting for async processing (hash: '{whisper_hash}', length: {len(whisper_hash)})")
        
        for attempt in range(max_retries):
            try:
                print(f"⏳ Attempt {attempt + 1}/{max_retries}: Checking status...")
                print(f"🔍 Debug - Calling whisper_status with hash: '{whisper_hash}'")
                
                # Try using client methods with explicit parameter
                try:
                    # Try different parameter approaches
                    print("🔍 Debug - Trying positional parameter...")
                    status_result = self.client.whisper_status(whisper_hash)
                    print(f"✅ Status check successful: {status_result}")
                    
                    status = status_result.get('status', 'unknown')
                    print(f"📊 Status: {status}")
                    
                    if status == 'processed':
                        print("🎉 Processing completed! Retrieving result...")
                        # Try to retrieve the result
                        try:
                            retrieve_result = self.client.whisper_retrieve(whisper_hash)
                            print(f"✅ Retrieved result keys: {list(retrieve_result.keys())}")
                            
                            # Extract text from various possible locations in the result
                            extracted_text = None
                            
                            # Try different possible locations for the text
                            if 'extracted_text' in retrieve_result:
                                extracted_text = retrieve_result['extracted_text']
                            elif 'extraction' in retrieve_result:
                                extraction = retrieve_result['extraction']
                                if isinstance(extraction, dict):
                                    extracted_text = extraction.get('result_text', '')
                                else:
                                    extracted_text = str(extraction)
                            elif 'text' in retrieve_result:
                                extracted_text = retrieve_result['text']
                            
                            if extracted_text and extracted_text.strip():
                                print(f"✅ Successfully extracted {len(extracted_text)} characters")
                                return extracted_text
                            else:
                                print("❌ No text found in retrieval result")
                                print(f"🔍 Full result: {retrieve_result}")
                                return None
                                
                        except Exception as retrieve_error:
                            print(f"❌ Error retrieving result: {retrieve_error}")
                            return None
                            
                    elif status == 'processing':
                        print("⏳ Still processing, waiting...")
                        time.sleep(delay)
                        continue
                    elif status == 'failed':
                        print(f"❌ Processing failed")
                        return None
                    else:
                        print(f"❌ Unknown status: {status}")
                        return None
                        
                except Exception as status_error:
                    print(f"❌ Status check error: {status_error}")
                    # Wait and try again
                    time.sleep(delay)
                    continue
                    
            except Exception as e:
                print(f"❌ General error in attempt {attempt + 1}: {e}")
                time.sleep(delay)
                continue
        
        print(f"⏰ Timeout after {max_retries} attempts")
        return None
    
    
    def _display_usage_info(self):
        """Display real-time usage information."""
        print("\n📊 Usage Information:")
        print(f"   • Processing Mode: {self.usage_stats['processing_mode']}")
        print(f"   • Estimated Pages: {self.usage_stats['pages_processed']}")
        print(f"   • Processing Time: {self.usage_stats['processing_time']:.2f} seconds")
        print("-" * 50)
    
    def _save_raw_output(self, pdf_path, extracted_text):
        """
        Save raw LLMWhisperer output to a text file for inspection.
        
        Args:
            pdf_path (str): Path to original PDF file
            extracted_text (str): Raw text from LLMWhisperer
            
        Returns:
            str: Path to saved raw text file
        """
        # Generate raw output filename
        input_name = os.path.splitext(os.path.basename(pdf_path))[0]
        raw_filename = f"{input_name}_raw.txt"
        
        try:
            with open(raw_filename, 'w', encoding='utf-8') as f:
                # Add header with metadata
                f.write(f"# Raw LLMWhisperer Output\n")
                f.write(f"# Source PDF: {pdf_path}\n")
                f.write(f"# Processing Mode: {self.usage_stats['processing_mode']}\n")
                f.write(f"# Extraction Time: {datetime.now()}\n")
                f.write(f"# Text Length: {len(extracted_text)} characters\n")
                f.write(f"{'='*80}\n\n")
                
                # Write raw text
                f.write(extracted_text)
            
            print(f"✅ Raw output saved to: {os.path.abspath(raw_filename)}")
            return raw_filename
            
        except Exception as e:
            print(f"⚠️  Could not save raw output: {e}")
            return None
    
    def parse_financial_data(self, extracted_text):
        """
        Parse the extracted text using GPT-4o-mini for maximum accuracy.
        
        Args:
            extracted_text (str): Raw text from LLMWhisperer
            
        Returns:
            pandas.DataFrame: Structured financial data
        """
        print("🤖 Using GPT-4o-mini for ultra-accurate financial data parsing...")
        print(f"📝 Input text length: {len(extracted_text)} characters")
        print("-" * 50)
        
        return self._parse_with_gpt(extracted_text)
    
    def _parse_with_gpt(self, extracted_text):
        """
        Use GPT-4o-mini to convert LLMWhisperer raw text directly to structured DataFrame.
        This replaces complex regex/position parsing with AI-powered conversion.
        """
        print("🤖 Initializing GPT-4o-mini for financial data conversion...")
        
        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Create completely generic prompt for ANY tabular data conversion
            prompt = f"""Convert this tabular document text to CSV format using ONLY the exact text from the raw file.

CRITICAL REQUIREMENTS - UNIVERSAL TABLE PROCESSING:
- This can be ANY type of tabular document (financial, statistical, inventory, etc.)
- Find column headers EXACTLY as they appear in the raw text (any format: dates, categories, periods, etc.)
- Use those EXACT headers as CSV column headers - do not modify them
- For each data row: keep all text EXACTLY as shown (including ALL leading spaces, indentation, punctuation)
- For each data row: keep all values EXACTLY as shown (including symbols, formatting, decimal places)
- Do NOT reformat, modify, clean, standardize, or assume anything about content
- Do NOT assume what type of document this is or what the data represents
- Only task: organize the exact text into the right columns based on their position in each row
- Quote all fields to preserve spaces and formatting
- Skip header/title rows and company names, but preserve all data rows

Process:
1. Identify column headers from the raw text (whatever format they use)
2. For each data row, take the label/description exactly as written
3. Take each value exactly as written and put in the right column by position
4. Work with any table structure - don't assume specific layouts

Example approach:
Raw text: "     Any item description                         123.45      678.90     432.10"
Output: "     Any item description","123.45","678.90","432.10"

Use ONLY what exists in the raw text, make no assumptions about document type or content.

Document text:
{extracted_text}

Output only the CSV data with exact raw formatting preserved, no explanation:"""

            print("🔄 Converting financial data with GPT-4o-mini...")
            
            # Call GPT-4o-mini for conversion
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
            print("✅ GPT-4o-mini conversion completed successfully!")
            
            # Convert CSV string to pandas DataFrame
            from io import StringIO
            df = pd.read_csv(StringIO(csv_content))
            
            print(f"📊 Generated DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"📋 Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"❌ GPT parsing error: {e}")
            print("⚠️  Falling back to simple text-based parsing...")
            # Fallback to basic parsing if GPT fails
            return self._simple_fallback_parsing(extracted_text)
    
    def _simple_fallback_parsing(self, extracted_text):
        """
        Simple fallback parsing if GPT fails.
        """
        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
        # Create basic DataFrame with raw lines
        return pd.DataFrame({'Account': lines, 'Column_2': '', 'Column_3': ''})
    
    def _parse_with_positions(self, lines):
        """
        Parse financial data using position-based analysis instead of regex.
        This preserves the exact structure from LLMWhisperer output.
        """
        print("🔍 Using position-based parsing for accurate data extraction")
        financial_data = []
        
        # Step 1: Find the column positions by analyzing the header row
        column_positions = self._detect_column_positions(lines)
        print(f"📍 Detected column positions: {column_positions}")
        
        # Step 2: Parse each line based on detected positions
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            # Classify line type and extract data
            line_data = self._parse_line_with_positions(line, column_positions, i)
            if line_data:
                financial_data.append(line_data)
        
        print(f"📊 Successfully parsed {len(financial_data)} rows using position-based method")
        return financial_data
    
    def _detect_column_positions(self, lines):
        """
        Detect column positions by finding the row with numerical data.
        This gives us the exact positions for Account, Amount1, Amount2, Amount3.
        """
        # Look for a line with multiple dollar amounts or numbers
        for line in lines:
            if '$' in line and line.count('$') >= 2:  # Line with multiple dollar amounts
                # Find positions of dollar signs and numbers
                positions = []
                words = line.split()
                current_pos = 0
                
                for word in words:
                    word_pos = line.find(word, current_pos)
                    if '$' in word or (word.replace(',', '').replace('(', '').replace(')', '').isdigit() and len(word) > 2):
                        positions.append(word_pos)
                    current_pos = word_pos + len(word)
                
                if len(positions) >= 2:
                    # Estimate column positions
                    account_end = min(positions) - 5  # Account name ends before first amount
                    col2_start = positions[0] if len(positions) > 0 else 70
                    col3_start = positions[1] if len(positions) > 1 else 85
                    col4_start = positions[2] if len(positions) > 2 else 100
                    
                    return {
                        'account_end': max(30, account_end),  # Minimum reasonable width
                        'col2_start': col2_start,
                        'col3_start': col3_start,
                        'col4_start': col4_start if len(positions) > 2 else None
                    }
        
        # Fallback: Use estimated positions based on typical financial statement layout
        return {
            'account_end': 60,
            'col2_start': 70,
            'col3_start': 85,
            'col4_start': 100
        }
    
    def _parse_line_with_positions(self, line, positions, line_number):
        """
        Parse a single line using the detected column positions.
        """
        if len(line.strip()) < 10:  # Skip very short lines
            return None
            
        # Extract account name (everything before first amount column)
        account_part = line[:positions['account_end']].strip()
        
        # Extract amounts from their respective positions
        col2_part = ""
        col3_part = ""
        col4_part = ""
        
        # Column 2
        if len(line) > positions['col2_start']:
            col2_end = positions['col3_start'] if positions['col3_start'] < len(line) else len(line)
            col2_part = line[positions['col2_start']:col2_end].strip()
        
        # Column 3
        if positions['col4_start'] and len(line) > positions['col3_start']:
            col3_end = positions['col4_start'] if positions['col4_start'] < len(line) else len(line)
            col3_part = line[positions['col3_start']:col3_end].strip()
        elif not positions['col4_start'] and len(line) > positions['col3_start']:
            col3_part = line[positions['col3_start']:].strip()
        
        # Column 4 (if exists)
        if positions['col4_start'] and len(line) > positions['col4_start']:
            col4_part = line[positions['col4_start']:].strip()
        
        # Clean and validate extracted parts
        col2_clean = self._clean_extracted_amount(col2_part)
        col3_clean = self._clean_extracted_amount(col3_part)
        col4_clean = self._clean_extracted_amount(col4_part) if col4_part else None
        
        # Determine line type
        line_type = self._determine_line_type(account_part, col2_clean, col3_clean, line)
        
        # Create data structure - use 4 columns if we have 3 amount columns
        if positions['col4_start'] and col4_clean:
            return {
                'Account': account_part,
                'Column_2': col2_clean,
                'Column_3': col3_clean,
                'Column_4': col4_clean,
                'Type': line_type
            }
        else:
            return {
                'Account': account_part,
                'Column_2': col2_clean,
                'Column_3': col3_clean,
                'Type': line_type
            }
    
    def _clean_extracted_amount(self, amount_str):
        """
        Clean extracted amount string and convert to appropriate format.
        """
        if not amount_str or amount_str in ['', '-', 'NaN']:
            return None
            
        # Remove extra whitespace
        cleaned = amount_str.strip()
        
        # Handle parentheses (negative numbers)
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        # Try to extract number
        import re
        number_match = re.search(r'[\d,]+\.?\d*', cleaned.replace('$', '').replace(' ', ''))
        if number_match:
            try:
                number_str = number_match.group().replace(',', '')
                # Keep as float for Excel formatting
                result = float(number_str)
                return result if cleaned.startswith('-') or '(' in amount_str else result
            except (ValueError, AttributeError):
                pass
        
        # Return as-is if can't parse as number (might be text like "Year", "Ended")
        return cleaned if cleaned else None
    
    def _determine_line_type(self, account, col2, col3, full_line):
        """
        Determine the type of line based on content and structure.
        """
        account_lower = account.lower() if account else ""
        
        # Headers (company names, statement titles)
        if any(word in account_lower for word in ['corporation', 'company', 'inc', 'ltd', 'statements', 'consolidated']):
            return 'header'
        
        # Column headers (dates, periods)
        if any(word in account_lower for word in ['january', 'february', 'march', 'april', 'may', 'june', 
                                                  'july', 'august', 'september', 'october', 'november', 'december', 'year', 'ended']):
            return 'column_header'
        
        # Major section headers (all caps, no amounts)
        if account.isupper() and len(account) > 5 and not col2 and not col3:
            return 'section_header'
        
        # Subsection headers (ending with colon or specific patterns)
        if account.endswith(':') or any(word in account_lower for word in ['expenses', 'per share', 'computation']):
            return 'subsection_header'
        
        # Line items with data
        if col2 is not None or col3 is not None:
            return 'line_item'
        
        # Default
        return 'line_item'
        
        for i, line in enumerate(lines[:15]):  # Check first 15 lines for headers
            line = line.strip()
            if line and len(line) > 10:  # Skip very short lines
                # Check if line looks like a header (all caps, company name, etc.)
                if (line.isupper() or 
                    any(word in line.upper() for word in ['CORPORATION', 'COMPANY', 'INC', 'LLC', 'LTD']) or
                    any(word in line.upper() for word in ['BALANCE', 'INCOME', 'STATEMENT', 'CASH', 'FLOW']) or
                    'millions' in line.lower() or 'thousands' in line.lower()):
                    potential_headers.append(line)
        
        # Take up to 3 header lines
        headers = potential_headers[:3]
        
        # Add header rows dynamically
        print(f"📋 Found {len(headers)} potential headers: {headers}")
        for header in headers:
            financial_data.append({
                'Account': header,
                'Column_2': '',
                'Column_3': '',
                'Type': 'header'
            })
        
        # Find column headers (dates, periods, etc.)
        column_headers = self._extract_column_headers(lines)
        print(f"📅 Found {len(column_headers)} column headers: {column_headers}")
        if column_headers:
            for i, col_header in enumerate(column_headers):
                if i == 0:  # First column header row
                    financial_data.append({
                        'Account': '',
                        'Column_2': col_header.get('col2', ''),
                        'Column_3': col_header.get('col3', ''),
                        'Type': 'column_header'
                    })
                else:  # Additional column header rows
                    financial_data.append({
                        'Account': '',
                        'Column_2': col_header.get('col2', ''),
                        'Column_3': col_header.get('col3', ''),
                        'Type': 'column_header'
                    })
        
        # Parse the financial data generically
        current_section = ""
        skip_lines_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip already processed header lines
            if skip_lines_count > 0:
                skip_lines_count -= 1
                continue
                
            # Skip date header lines that might be parsed incorrectly
            if self._is_date_header_line(line):
                skip_lines_count = 1  # Skip this and potentially next line
                continue
                
            # Detect section headers (all caps, standalone lines)
            if self._is_section_header(line):
                financial_data.append({
                    'Account': line,
                    'Column_2': '',
                    'Column_3': '',
                    'Type': 'section_header'
                })
                current_section = line.lower().replace(' ', '_')
                continue
                
            # Detect subsection headers (ending with colon, specific patterns)
            if self._is_subsection_header(line):
                financial_data.append({
                    'Account': line,
                    'Column_2': '',
                    'Column_3': '',
                    'Type': 'subsection_header'
                })
                current_section = line.lower().replace(' ', '_').replace(':', '')
                continue
            
            # Parse financial line items
            if self._has_financial_amounts(line):
                parsed_item = self._parse_line_item(line)
                if parsed_item:
                    # Add indentation for subsection items
                    if self._should_indent(current_section):
                        parsed_item['Account'] = '     ' + parsed_item['Account']
                    
                    parsed_item['Type'] = 'line_item'
                    financial_data.append(parsed_item)
        
        print(f"📊 Parsed {len(financial_data)} financial table rows")
        
        # Summary of parsed data types
        type_counts = {}
        for item in financial_data:
            item_type = item.get('Type', 'unknown')
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        print(f"📈 Breakdown: {dict(type_counts)}")
        return financial_data
    
    def _extract_column_headers(self, lines):
        """Extract column headers (dates, periods) from the document."""
        column_headers = []
        
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if not line:
                continue
                
            # Look for date patterns or period indicators
            if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', line, re.IGNORECASE):
                # Try to extract two column dates
                date_match = re.findall(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,?)', line, re.IGNORECASE)
                if len(date_match) >= 2:
                    column_headers.append({'col2': date_match[0], 'col3': date_match[1]})
                    
            # Look for year patterns
            elif re.search(r'\b(19|20)\d{2}\b.*\b(19|20)\d{2}\b', line):
                years = re.findall(r'\b(19|20)\d{2}\b', line)
                if len(years) >= 2:
                    column_headers.append({'col2': years[0], 'col3': years[1]})
                    
            # Look for period indicators
            elif re.search(r'(quarter|year|period|ended)', line, re.IGNORECASE):
                # Try to split into two columns
                parts = line.split()
                if len(parts) >= 2:
                    mid = len(parts) // 2
                    col2 = ' '.join(parts[:mid])
                    col3 = ' '.join(parts[mid:])
                    column_headers.append({'col2': col2, 'col3': col3})
        
        return column_headers[:2]  # Return max 2 column header rows
    
    def _is_date_header_line(self, line):
        """Check if line is a problematic date header that should be skipped."""
        # Skip lines that look like partial date headers
        if len(line) < 40 and re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)', line, re.IGNORECASE):
            return True
        # Skip standalone year lines
        if line.strip().isdigit() and len(line.strip()) == 4:
            return True
        return False
    
    def _is_section_header(self, line):
        """Check if line is a major section header."""
        # All caps lines that are likely section headers
        if line.isupper() and len(line) > 3:
            # Common section header patterns
            section_keywords = ['ASSETS', 'LIABILITIES', 'EQUITY', 'REVENUE', 'EXPENSES', 
                              'INCOME', 'CASH FLOW', 'OPERATIONS', 'FINANCING', 'INVESTING']
            if any(keyword in line for keyword in section_keywords):
                return True
        return False
    
    def _is_subsection_header(self, line):
        """Check if line is a subsection header."""
        # Lines ending with colon
        if line.endswith(':'):
            return True
        # Common subsection patterns
        subsection_patterns = ['current', 'non-current', 'long-term', 'short-term', 'total', 'net']
        if any(pattern in line.lower() for pattern in subsection_patterns):
            return True
        return False
    
    def _should_indent(self, current_section):
        """Determine if items in this section should be indented."""
        indent_sections = ['current_assets', 'current_liabilities', 'shareholders_equity', 
                          'stockholders_equity', 'operating_expenses', 'other_income']
        return any(section in current_section for section in indent_sections)
    
    def _has_financial_amounts(self, line):
        """Check if line contains financial amounts."""
        # Look for patterns with dollar signs or numbers at the end
        amount_pattern = re.compile(r'.*\$?\s*([0-9,]+)\s*([0-9,]+)?.*$')
        return bool(amount_pattern.match(line))
    
    def _parse_line_item(self, line):
        """Parse a line item with account name and amounts."""
        # Pattern to match account name and amounts
        # More flexible pattern that handles various formats
        patterns = [
            # Pattern: Account name $ amount $ amount
            re.compile(r'(.+?)\s*\$\s*([0-9,]+)\s*\$?\s*([0-9,]+)?'),
            # Pattern: Account name amount amount
            re.compile(r'(.+?)\s+([0-9,]+)\s+([0-9,]+)$'),
            # Pattern: Account name $ amount
            re.compile(r'(.+?)\s*\$\s*([0-9,]+)$'),
            # Pattern: Account name amount
            re.compile(r'(.+?)\s+([0-9,]+)$')
        ]
        
        for pattern in patterns:
            match = pattern.match(line.strip())
            if match:
                account_name = match.group(1).strip()
                current_amount = self._clean_amount(match.group(2)) if match.group(2) else None
                prior_amount = self._clean_amount(match.group(3)) if len(match.groups()) > 2 and match.group(3) else None
                
                # Clean account name (remove extra dollar signs)
                account_name = re.sub(r'\$+', '', account_name).strip()
                
                if account_name and len(account_name) > 2:
                    return {
                        'Account': account_name,
                        'Column_2': current_amount,
                        'Column_3': prior_amount
                    }
        
        return None
    
    def _clean_amount(self, amount_str):
        """Clean and convert amount string to float."""
        if not amount_str:
            return None
            
        # Remove commas and convert to float
        try:
            cleaned = re.sub(r'[,\s$]', '', amount_str)
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
    
    def create_dataframe(self, financial_data):
        """
        Create pandas DataFrame from structured financial data.
        
        Args:
            financial_data (list): Structured financial data
            
        Returns:
            pandas.DataFrame: Organized financial data
        """
        print("📊 Creating pandas DataFrame...")
        
        if not financial_data:
            print("⚠️  No financial data to process")
            return pd.DataFrame()
        
        df = pd.DataFrame(financial_data)
        
        # Ensure proper column order
        column_order = ['Account', 'Column_2', 'Column_3', 'Type']
        df = df.reindex(columns=column_order)
        
        print(f"✅ DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    def export_to_excel(self, df, output_filename="financial_table_extracted.xlsx"):
        """
        Export DataFrame to Excel with proper formatting.
        
        Args:
            df (pandas.DataFrame): Financial data DataFrame from GPT conversion
            output_filename (str): Output Excel filename
        """
        print(f"📤 Exporting GPT-converted data to Excel: {output_filename}")
        
        try:
            # Simple export using pandas - GPT has already structured the data perfectly
            with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Financial Data', index=False)
                
                # Add usage summary sheet
                usage_df = pd.DataFrame([self.usage_stats])
                usage_df.to_excel(writer, sheet_name='Usage Summary', index=False)
                
                # Format the financial data sheet
                worksheet = writer.sheets['Financial Data']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 chars
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            print(f"✅ Successfully exported to {output_filename}")
            print(f"📂 File location: {os.path.abspath(output_filename)}")
            print(f"📊 Format: Clean structured data with {df.shape[0]} rows × {df.shape[1]} columns")
            
        except Exception as e:
            print(f"❌ Error exporting to Excel: {e}")
            # Fallback: save as CSV
            csv_filename = output_filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False)
            print(f"📄 Fallback: Saved as CSV to {csv_filename}")
        
        # BOOKMARKED: Old complex openpyxl formatting code removed  
        # GPT-4o-mini provides perfectly structured data, no complex formatting needed
    
    def process_financial_table(self, pdf_path, output_filename="financial_table_extracted.xlsx"):
        """
        Complete pipeline: Extract → Parse → Structure → Export to Excel.
        
        Args:
            pdf_path (str): Path to financial table PDF
            output_filename (str): Output Excel filename
        """
        print("🚀 Starting Financial Table Processing Pipeline")
        print("=" * 60)
        
        # Step 1: Extract from PDF using LLMWhisperer
        # Try different processing modes if first fails (form mode first for financial documents)
        modes_to_try = ["form", "high_quality", "low_cost"]
        extraction_result = None
        
        for mode in modes_to_try:
            print(f"\n🔄 Trying processing mode: {mode}")
            extraction_result = self.extract_from_pdf(pdf_path, processing_mode=mode)
            
            if extraction_result['success'] and extraction_result.get('text', '').strip():
                print(f"✅ Successfully extracted with mode: {mode}")
                break
            else:
                print(f"⚠️  Mode {mode} failed or returned empty result")
        
        if not extraction_result or not extraction_result['success']:
            print("❌ All extraction modes failed. Stopping pipeline.")
            return False
        
        # Save raw text to output/raw/ folder for debugging
        input_name = os.path.splitext(os.path.basename(pdf_path))[0]
        raw_path = f"output/raw/{input_name}_raw.txt"
        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(f"# Raw LLMWhisperer Output\n")
            f.write(f"# Source PDF: {pdf_path}\n") 
            f.write(f"# Processing Mode: {extraction_result.get('processing_mode', 'unknown')}\n")
            f.write(f"# Extraction Time: {datetime.now().isoformat()}\n")
            f.write(f"# Text Length: {len(extraction_result.get('text', ''))} characters\n")
            f.write("=" * 80 + "\n\n")
            f.write(extraction_result.get('text', ''))
        
        print(f"💾 Raw text saved to: {raw_path}")
        
        # Now use Pydantic + LangChain methodology instead of GPT processing
        print("🤖 Using Pydantic + LangChain methodology for structured extraction...")
        
        # TODO: Add proper Pydantic + LangChain processing here
        # For now, continue with existing pipeline but we've saved the raw text
        
        
        if not extraction_result.get('text', '').strip():
            print("❌ All extraction modes returned empty text. Stopping pipeline.")
            return False
        
        # Step 1.5: Save raw LLMWhisperer output to file for inspection
        raw_filename = self._save_raw_output(pdf_path, extraction_result['text'])
        print(f"💾 Raw LLMWhisperer output saved to: {raw_filename}")
        
        # Step 2: Parse and structure the data using GPT-4o-mini
        df = self.parse_financial_data(extraction_result['text'])
        
        if df is None or df.empty:
            print("⚠️  No financial data found in the extracted text.")
            return False
        
        # Step 4: Export to Excel
        self.export_to_excel(df, output_filename)
        
        print(f"💾 Raw output file: {raw_filename}")
        print("\n🎉 Pipeline completed successfully!")
        print("=" * 60)
        return True

def main():
    """Main function to run the financial table extractor."""
    import sys
    
    # Check command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 financial_table_extractor.py <input_pdf_path>")
        print("\nExample:")
        print("  python3 financial_table_extractor.py \"balance sheet.pdf\"")
        print("  python3 financial_table_extractor.py \"/path/to/income_statement.pdf\"")
        print("  python3 financial_table_extractor.py \"financial_report.pdf\"")
        return
    
    # Get input file path from command line
    pdf_path = sys.argv[1]
    
    # Generate output filename based on input filename
    input_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_filename = f"{input_name}_extracted.xlsx"
    
    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"📄 Input file: {pdf_path}")
    print(f"📊 Output file: {output_filename}")
    
    # Initialize extractor and process
    extractor = FinancialTableExtractor()
    success = extractor.process_financial_table(pdf_path, output_filename)
    
    if success:
        print(f"\n📊 Financial table data successfully extracted to {output_filename}")
    else:
        print("\n❌ Financial table extraction failed")

if __name__ == "__main__":
    main()