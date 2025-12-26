"""
JSON to Excel converter that preserves structure and formatting.
Converts structured JSON output to Excel while maintaining indentation and formatting.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import os
import sys
import re
from openpyxl.styles import Font


class StructuredJSONToExcelConverter:
    """Converts structured financial JSON to Excel with preserved formatting."""
    
    def __init__(self):
        """Initialize the converter."""
        pass
    
    def parse_structured_json(self, json_file_path: str) -> Dict[str, Any]:
        """
        Parse the structured JSON file and extract the inner JSON data.
        
        Args:
            json_file_path (str): Path to the structured JSON file
            
        Returns:
            Dict[str, Any]: Parsed financial data
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            outer_data = json.load(f)
        
        # The actual financial data is in the 'extracted_data' field as JSON string
        extracted_data_str = outer_data['extracted_data']
        
        # Remove markdown code blocks if present
        if '```json' in extracted_data_str:
            extracted_data_str = extracted_data_str.replace('```json', '').replace('```', '').strip()
        
        # Parse the inner JSON
        financial_data = json.loads(extracted_data_str)
        
        # Add metadata
        financial_data['metadata'] = {
            'document_type': outer_data['document_type'],
            'schema_used': outer_data['schema_used'],
            'processing_time': outer_data['processing_time'],
            'extraction_timestamp': outer_data['extraction_timestamp']
        }
        
        return financial_data
    
    def create_excel_from_structured_data(self, financial_data: Dict[str, Any], output_path: str) -> str:
        """
        Create Excel file from structured financial data while preserving formatting.
        
        Args:
            financial_data (Dict[str, Any]): Parsed financial data
            output_path (str): Output Excel file path
            
        Returns:
            str: Path to created Excel file
        """
        # Create Excel writer with formatting options
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            
            # Sheet 1: Financial Data
            self._create_financial_data_sheet(financial_data, writer)
            
            # Sheet 2: Metadata
            self._create_metadata_sheet(financial_data, writer)
            
            print(f"📊 Excel file created: {os.path.abspath(output_path)}")
        
        return output_path
    
    def _create_financial_data_sheet(self, financial_data: Dict[str, Any], writer):
        """Create the main financial data sheet."""
        
        # Extract data components
        document_title = financial_data.get('document_title', 'Financial Statement')
        reporting_periods = financial_data.get('reporting_periods', [])
        line_items = financial_data.get('line_items', [])
        
        # Create DataFrame structure
        data_rows = []
        
        # Add title row
        title_row = [document_title] + [''] * len(reporting_periods)
        data_rows.append(title_row)
        
        # Add empty row for spacing
        data_rows.append([''] * (len(reporting_periods) + 1))
        
        # Add header row
        header_row = ['Account'] + reporting_periods
        data_rows.append(header_row)
        
        # Add line items
        for item in line_items:
            account_name = item.get('account_name', '')
            
            # Build row with all periods
            row = [account_name]
            
            # Add values for each period (handling different schema field names)
            if 'current_year' in item:  # Income statement schema
                row.extend([
                    item.get('current_year', ''),
                    item.get('previous_year', ''),
                    item.get('third_year', '')
                ][:len(reporting_periods)])
            elif 'current_period' in item:  # Other schema types
                row.extend([
                    item.get('current_period', ''),
                    item.get('previous_period', ''),
                    item.get('third_period', '')
                ][:len(reporting_periods)])
            else:
                # Fallback: fill with empty strings
                row.extend([''] * len(reporting_periods))
            
            # Ensure row has correct length
            while len(row) < len(reporting_periods) + 1:
                row.append('')
            
            data_rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Write to Excel
        df.to_excel(writer, sheet_name='Financial Data', index=False, header=False)
        
        # Apply formatting
        workbook = writer.book
        worksheet = writer.sheets['Financial Data']
        
        # Format title (row 1)
        title_cell = worksheet['A1']
        title_cell.font = Font(bold=True, size=14)
        
        # Format headers (row 3)
        for col_num in range(len(header_row)):
            cell = worksheet.cell(row=3, column=col_num + 1)
            cell.font = Font(bold=True)
        
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
            
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _create_metadata_sheet(self, financial_data: Dict[str, Any], writer):
        """Create metadata information sheet."""
        
        metadata = financial_data.get('metadata', {})
        
        metadata_rows = [
            ['Document Type', metadata.get('document_type', 'Unknown')],
            ['Schema Used', metadata.get('schema_used', 'Unknown')],
            ['Processing Time (seconds)', metadata.get('processing_time', 'Unknown')],
            ['Extraction Timestamp', metadata.get('extraction_timestamp', 'Unknown')],
            [''],
            ['Document Title', financial_data.get('document_title', 'Not specified')],
            ['Reporting Periods', ', '.join(financial_data.get('reporting_periods', []))],
            ['Number of Line Items', len(financial_data.get('line_items', []))]
        ]
        
        df_metadata = pd.DataFrame(metadata_rows, columns=['Property', 'Value'])
        df_metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        # Format metadata sheet
        worksheet = writer.sheets['Metadata']
        
        # Make first column bold
        for row_num in range(1, len(metadata_rows) + 2):
            cell = worksheet.cell(row=row_num, column=1)
            cell.font = Font(bold=True)
        
        # Auto-adjust column widths
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 40
    
    def convert_json_to_excel(self, json_file_path: str, excel_output_path: str = None) -> str:
        """
        Main method to convert structured JSON to Excel.
        
        Args:
            json_file_path (str): Path to input JSON file
            excel_output_path (str): Optional output Excel path
            
        Returns:
            str: Path to created Excel file
        """
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        # Generate output path if not provided
        if not excel_output_path:
            base_name = os.path.splitext(os.path.basename(json_file_path))[0]
            excel_output_path = f"{base_name}_formatted.xlsx"
        
        print(f"🔄 Converting JSON to Excel...")
        print(f"📂 Input: {json_file_path}")
        print(f"📊 Output: {excel_output_path}")
        
        # Parse structured JSON
        financial_data = self.parse_structured_json(json_file_path)
        
        # Create Excel file
        excel_path = self.create_excel_from_structured_data(financial_data, excel_output_path)
        
        print(f"✅ Conversion completed successfully!")
        
        return excel_path


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python3 json_to_excel_converter.py <json_file_path> [excel_output_path]")
        print("\nExample:")
        print('  python3 json_to_excel_converter.py "income statement_structured.json"')
        print('  python3 json_to_excel_converter.py "income statement_structured.json" "output.xlsx"')
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    excel_output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    converter = StructuredJSONToExcelConverter()
    
    try:
        excel_path = converter.convert_json_to_excel(json_file_path, excel_output_path)
        print(f"\n📄 Excel file ready: {excel_path}")
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()