"""
Batch processing capability for multiple financial documents.
Processes all PDFs in a directory using the structured extractor.
"""

import os
import sys
import glob
from datetime import datetime
from typing import List, Dict, Any
from structured_extractor import StructuredFinancialExtractor


class BatchFinancialProcessor:
    """Batch processes multiple financial documents using structured extraction."""
    
    def __init__(self):
        """Initialize the batch processor."""
        self.extractor = StructuredFinancialExtractor()
        self.results = []
        self.start_time = None
        self.end_time = None
        
        # Ensure output directories exist
        self._ensure_output_directories()
    
    def _ensure_output_directories(self):
        """Ensure the organized output directory structure exists."""
        directories = [
            "output/structured/json",
            "output/structured/excel", 
            "output/structured/reports",
            "output/legacy"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def process_directory(self, input_directory: str, output_directory: str = None) -> List[Dict[str, Any]]:
        """
        Process all PDF files in a directory.
        
        Args:
            input_directory (str): Directory containing PDF files
            output_directory (str): Optional output directory for results
            
        Returns:
            List[Dict[str, Any]]: List of processing results
        """
        print("🚀 Starting Batch Financial Document Processing")
        print("=" * 60)
        
        if not os.path.exists(input_directory):
            raise FileNotFoundError(f"Input directory not found: {input_directory}")
        
        # Create output directory if specified
        if output_directory and not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"📁 Created output directory: {output_directory}")
        
        # Find all PDF files
        pdf_pattern = os.path.join(input_directory, "*.pdf")
        pdf_files = glob.glob(pdf_pattern)
        
        if not pdf_files:
            print(f"⚠️ No PDF files found in {input_directory}")
            return []
        
        print(f"📄 Found {len(pdf_files)} PDF files to process")
        self.start_time = datetime.now()
        
        # Process each PDF file
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n📊 Processing {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
            
            try:
                # Process the document
                result = self.extractor.process_financial_document(pdf_file)
                
                # Save JSON output
                json_output = self._save_json_output(pdf_file, result, output_directory)
                
                # Save Excel output  
                excel_output = self._save_excel_output(pdf_file, json_output, output_directory)
                
                # Store result summary
                result_summary = {
                    'file_name': os.path.basename(pdf_file),
                    'file_path': pdf_file,
                    'success': result['success'],
                    'document_type': result['document_type'],
                    'schema_used': result['schema_used'],
                    'line_items_count': len(result['parsed_data'].line_items) if hasattr(result['parsed_data'], 'line_items') else 0,
                    'processing_time': result['usage_stats']['processing_time'],
                    'json_output': json_output,
                    'excel_output': excel_output
                }
                
                self.results.append(result_summary)
                print(f"✅ Successfully processed: {result['document_type']} with {result_summary['line_items_count']} line items")
                
            except Exception as e:
                error_result = {
                    'file_name': os.path.basename(pdf_file),
                    'file_path': pdf_file,
                    'success': False,
                    'error': str(e),
                    'document_type': 'unknown',
                    'schema_used': 'none',
                    'line_items_count': 0,
                    'processing_time': 0,
                    'json_output': None,
                    'excel_output': None
                }
                self.results.append(error_result)
                print(f"❌ Failed to process {os.path.basename(pdf_file)}: {e}")
        
        self.end_time = datetime.now()
        
        # Generate summary report
        self._generate_summary_report(output_directory)
        
        print("\\n🎉 Batch processing completed!")
        print("=" * 60)
        
        return self.results
    
    def _save_json_output(self, pdf_file: str, result: Dict[str, Any], output_directory: str = None) -> str:
        """Save JSON output for a processed document."""
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        
        if output_directory:
            json_path = os.path.join(output_directory, f"{base_name}_structured.json")
        else:
            json_path = f"output/structured/json/{base_name}_structured.json"
        
        # Use the extractor's existing JSON saving functionality
        import json
        json_data = {
            'document_type': result['document_type'],
            'schema_used': result['schema_used'],
            'extracted_data': result['raw_response'],
            'processing_time': result['usage_stats']['processing_time'],
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return json_path
    
    def _save_excel_output(self, pdf_file: str, json_path: str, output_directory: str = None) -> str:
        """Save Excel output for a processed document."""
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        
        if output_directory:
            excel_path = os.path.join(output_directory, f"{base_name}_structured.xlsx")
        else:
            excel_path = f"output/structured/excel/{base_name}_structured.xlsx"
        
        # Use the JSON to Excel converter
        from json_to_excel_converter import StructuredJSONToExcelConverter
        converter = StructuredJSONToExcelConverter()
        converter.convert_json_to_excel(json_path, excel_path)
        
        return excel_path
    
    def _generate_summary_report(self, output_directory: str = None):
        """Generate a summary report of the batch processing."""
        
        # Calculate statistics
        total_files = len(self.results)
        successful_files = len([r for r in self.results if r['success']])
        failed_files = total_files - successful_files
        
        total_processing_time = sum(r['processing_time'] for r in self.results)
        total_line_items = sum(r['line_items_count'] for r in self.results)
        
        document_types = {}
        for result in self.results:
            if result['success']:
                doc_type = result['document_type']
                document_types[doc_type] = document_types.get(doc_type, 0) + 1
        
        batch_time = (self.end_time - self.start_time).total_seconds()
        
        # Create summary report
        report_lines = [
            "BATCH PROCESSING SUMMARY REPORT",
            "=" * 50,
            f"Batch Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Batch End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Batch Time: {batch_time:.2f} seconds",
            "",
            "PROCESSING STATISTICS:",
            f"Total Files Processed: {total_files}",
            f"Successful Extractions: {successful_files}",
            f"Failed Extractions: {failed_files}",
            f"Success Rate: {(successful_files/total_files)*100:.1f}%",
            "",
            f"Total Processing Time (LLM): {total_processing_time:.2f} seconds",
            f"Total Line Items Extracted: {total_line_items}",
            f"Average Line Items per Document: {total_line_items/successful_files:.1f}" if successful_files > 0 else "Average Line Items per Document: 0",
            "",
            "DOCUMENT TYPES PROCESSED:",
        ]
        
        for doc_type, count in document_types.items():
            report_lines.append(f"  {doc_type}: {count} documents")
        
        report_lines.extend([
            "",
            "INDIVIDUAL FILE RESULTS:",
            "-" * 50,
        ])
        
        for result in self.results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            if result['success']:
                report_lines.append(
                    f"{status} | {result['file_name']} | {result['document_type']} | "
                    f"{result['line_items_count']} items | {result['processing_time']:.2f}s"
                )
            else:
                report_lines.append(f"{status} | {result['file_name']} | Error: {result['error']}")
        
        report_text = "\\n".join(report_lines)
        
        # Save report to file
        if output_directory:
            report_path = os.path.join(output_directory, "batch_processing_report.txt")
        else:
            report_path = "output/structured/reports/batch_processing_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\\n📊 Summary report saved: {os.path.abspath(report_path)}")
        
        # Print key statistics to console
        print(f"\\n📈 Batch Processing Summary:")
        print(f"   Files Processed: {successful_files}/{total_files} ({(successful_files/total_files)*100:.1f}% success)")
        print(f"   Total Line Items: {total_line_items}")
        print(f"   Processing Time: {total_processing_time:.2f}s (LLM) + {batch_time:.2f}s (total)")


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python3 batch_processor.py <input_directory> [output_directory]")
        print("\\nExample:")
        print("  python3 batch_processor.py input/")
        print("  python3 batch_processor.py input/ custom_output/")
        print("\\nIf no output_directory specified, files are organized automatically:")
        print("  📄 JSON: output/structured/json/")
        print("  📊 Excel: output/structured/excel/")
        print("  📋 Reports: output/structured/reports/")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_directory):
        print(f"❌ Input directory not found: {input_directory}")
        sys.exit(1)
    
    # Initialize processor and run batch
    processor = BatchFinancialProcessor()
    
    try:
        results = processor.process_directory(input_directory, output_directory)
        
        if results:
            successful = len([r for r in results if r['success']])
            print(f"\\n✅ Batch processing completed!")
            print(f"   Successfully processed: {successful}/{len(results)} documents")
        else:
            print("\\n⚠️ No documents were processed")
            
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()