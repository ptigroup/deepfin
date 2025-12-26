#!/usr/bin/env python3
"""
AI-Powered Table Detection System using PyMuPDF

This module uses PyMuPDF's advanced table detection to identify financial statement tables
in PDF documents without using LLMWhisperer credits, then validates the content
to ensure proper financial statements are identified.
"""

import os
import re
import json
import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class FinancialStatementType(Enum):
    """Types of financial statements we can detect."""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    COMPREHENSIVE_INCOME = "comprehensive_income"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    UNKNOWN = "unknown"


@dataclass
class DetectedTable:
    """Represents a detected table with validation information."""
    page_number: int
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    statement_type: FinancialStatementType
    confidence_score: float
    content_indicators: Dict[str, Any]
    table_structure: Dict[str, Any]


class AITableDetector:
    """AI-powered table detector using PyMuPDF and advanced content validation."""
    
    def __init__(self):
        """Initialize the detector."""
        # Removed verbose message for production mode
        # Removed verbose message for production mode
    
    def detect_tables_in_pdf(self, pdf_path: str) -> Dict[int, List[DetectedTable]]:
        """
        Detect all tables in a PDF using PyMuPDF table detection.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping page numbers to lists of detected tables
        """
        print(f"🔍 Scanning PDF for tables: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Load PDF with PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            print(f"📄 Loaded PDF with {len(doc)} pages")
        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            return {}
        
        # Process results and find tables
        detected_tables = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_tables = []
            
            print(f"📊 Analyzing page {page_num + 1}...")
            
            try:
                # Find tables using PyMuPDF's built-in table detection
                table_finder = page.find_tables()
                tables = table_finder.tables
                
                print(f"🔎 Found {len(tables)} tables on page {page_num + 1}")
                
                for table_idx, table in enumerate(tables):
                    print(f"  🔍 Analyzing table {table_idx + 1} at {table.bbox}")
                    
                    # Extract table content
                    try:
                        table_data = table.extract()
                        table_content = self._table_data_to_text(table_data)
                        
                        # Get page text for additional context
                        page_text = page.get_text()
                        
                        # Combine table content with surrounding text for better validation
                        combined_content = f"{page_text}\n\n{table_content}"
                        
                        # Validate if this is a financial statement table
                        validation_result = self._validate_financial_content(combined_content, table_data)
                        
                        if validation_result['is_financial_table']:
                            detected_table = DetectedTable(
                                page_number=page_num + 1,
                                bbox=table.bbox,
                                statement_type=validation_result['statement_type'],
                                confidence_score=validation_result['confidence_score'],
                                content_indicators=validation_result['indicators'],
                                table_structure=validation_result['structure']
                            )
                            page_tables.append(detected_table)
                            print(f"    ✅ Validated financial table: {detected_table.statement_type.value} (confidence: {detected_table.confidence_score:.2f})")
                        else:
                            print(f"    ❌ Table rejected - not a financial statement (score: {validation_result['confidence_score']:.2f})")
                            
                    except Exception as e:
                        print(f"    ⚠️ Error extracting table {table_idx + 1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"⚠️ Error finding tables on page {page_num + 1}: {e}")
                continue
            
            if page_tables:
                detected_tables[page_num + 1] = page_tables
        
        doc.close()
        
        total_tables = sum(len(tables) for tables in detected_tables.values())
        print(f"🎯 Detection complete: Found {total_tables} validated financial tables across {len(detected_tables)} pages")
        
        return detected_tables
    
    def _table_data_to_text(self, table_data: List[List]) -> str:
        """
        Convert table data to text for analysis.
        
        Args:
            table_data: 2D list representing table rows and columns
            
        Returns:
            Text representation of the table
        """
        if not table_data:
            return ""
        
        # Convert table data to text format
        text_lines = []
        for row in table_data:
            if row:  # Skip empty rows
                # Join cells with pipe separator, similar to LLMWhisperer format
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                text_lines.append(row_text)
        
        return "\n".join(text_lines)
    
    def _validate_financial_content(self, combined_content: str, table_data: List[List] = None) -> Dict[str, Any]:
        """
        Validate if table content represents a financial statement.
        
        Args:
            combined_content: Combined text content (page + table)
            table_data: Raw table data for structural analysis
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_financial_table': False,
            'statement_type': FinancialStatementType.UNKNOWN,
            'confidence_score': 0.0,
            'indicators': {},
            'structure': {}
        }
        
        # Convert to lowercase for analysis
        content_lower = combined_content.lower()
        
        # Define financial statement indicators
        indicators = {
            FinancialStatementType.INCOME_STATEMENT: [
                'revenue', 'net income', 'operating expenses', 'cost of revenue',
                'gross profit', 'earnings per share', 'diluted shares'
            ],
            FinancialStatementType.BALANCE_SHEET: [
                'total assets', 'current assets', 'total liabilities', 'stockholders equity',
                'cash and cash equivalents', 'accounts receivable', 'retained earnings'
            ],
            FinancialStatementType.COMPREHENSIVE_INCOME: [
                'comprehensive income', 'other comprehensive income', 'foreign currency',
                'unrealized gains', 'total comprehensive income'
            ],
            FinancialStatementType.SHAREHOLDERS_EQUITY: [
                'common stock', 'additional paid-in capital', 'treasury stock',
                'accumulated other comprehensive', 'retained earnings', 'shares outstanding'
            ]
        }
        
        # Score each statement type
        type_scores = {}
        for stmt_type, keywords in indicators.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in content_lower:
                    score += 10
                    matched_keywords.append(keyword)
            
            type_scores[stmt_type] = {
                'score': score,
                'matched_keywords': matched_keywords
            }
        
        # Find highest scoring type
        best_type = max(type_scores, key=lambda x: type_scores[x]['score'])
        best_score = type_scores[best_type]['score']
        
        # Additional validation criteria
        bonus_score = 0
        
        # Check for financial data patterns
        dollar_amounts = len(re.findall(r'\$[\d,]+', combined_content))
        if dollar_amounts >= 3:
            bonus_score += 20
        
        # Check for multi-year structure
        years = len(re.findall(r'\b20\d{2}\b', combined_content))
        if years >= 2:
            bonus_score += 15
        
        # Check for proper table structure
        if table_data and len(table_data) >= 5:  # Minimum rows for a real statement
            bonus_score += 15
            
            # Check for multi-column structure (financial statements have multiple periods)
            if table_data and len(table_data[0]) >= 3:  # At least 3 columns
                bonus_score += 10
        
        # Check for sufficient content
        if len(combined_content.split('\n')) >= 10:  # Minimum lines for a real statement
            bonus_score += 10
        
        # Penalty for summary/percentage tables
        percentage_count = combined_content.count('%')
        if percentage_count > 10:
            bonus_score -= 30
        
        if 'analysis' in content_lower or 'summary' in content_lower:
            bonus_score -= 20
            
        # Check for financial statement title indicators
        title_indicators = [
            'consolidated statements', 'statement of income', 'balance sheet',
            'statements of operations', 'comprehensive income', 'stockholders equity'
        ]
        
        for title in title_indicators:
            if title in content_lower:
                bonus_score += 25
                break
        
        final_score = best_score + bonus_score
        
        # Determine if this is a valid financial table
        if final_score >= 30:  # Minimum threshold
            validation_result.update({
                'is_financial_table': True,
                'statement_type': best_type,
                'confidence_score': min(final_score / 100.0, 1.0),
                'indicators': {
                    'matched_keywords': type_scores[best_type]['matched_keywords'],
                    'dollar_amounts': dollar_amounts,
                    'year_count': years,
                    'line_count': len(combined_content.split('\n')),
                    'table_rows': len(table_data) if table_data else 0,
                    'table_columns': len(table_data[0]) if table_data and table_data[0] else 0
                },
                'structure': {
                    'has_multi_year': years >= 2,
                    'has_financial_data': dollar_amounts >= 3,
                    'sufficient_content': len(combined_content.split('\n')) >= 10,
                    'has_table_structure': table_data and len(table_data) >= 5 and len(table_data[0]) >= 3
                }
            })
        
        return validation_result
    
    def get_page_ranges_for_extraction(self, detected_tables: Dict[int, List[DetectedTable]]) -> Dict[FinancialStatementType, List[int]]:
        """
        Get page ranges for each financial statement type for targeted LLMWhisperer extraction.
        
        Args:
            detected_tables: Dictionary of detected tables by page
            
        Returns:
            Dictionary mapping statement types to page lists
        """
        page_ranges = {}
        
        for page_num, tables in detected_tables.items():
            for table in tables:
                stmt_type = table.statement_type
                
                if stmt_type not in page_ranges:
                    page_ranges[stmt_type] = []
                
                # Add current page and surrounding pages (statements often span multiple pages)
                for page_offset in [-1, 0, 1, 2]:
                    target_page = page_num + page_offset
                    if target_page > 0 and target_page not in page_ranges[stmt_type]:
                        page_ranges[stmt_type].append(target_page)
        
        # Sort page lists
        for stmt_type in page_ranges:
            page_ranges[stmt_type].sort()
        
        return page_ranges
    
    def save_detection_results(self, detected_tables: Dict[int, List[DetectedTable]], output_path: str) -> None:
        """
        Save detection results to JSON file for debugging and analysis.
        
        Args:
            detected_tables: Dictionary of detected tables
            output_path: Path to save the results
        """
        # Convert to serializable format
        serializable_results = {}
        
        for page_num, tables in detected_tables.items():
            serializable_results[page_num] = []
            
            for table in tables:
                table_data = {
                    'page_number': table.page_number,
                    'bbox': table.bbox,
                    'statement_type': table.statement_type.value,
                    'confidence_score': table.confidence_score,
                    'content_indicators': table.content_indicators,
                    'table_structure': table.table_structure
                }
                serializable_results[page_num].append(table_data)
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"✅ Detection results saved to: {output_path}")


def main():
    """Test the AI table detector."""
    # Test with one of the NVIDIA PDFs
    test_pdf = "input multiple/NVIDIA 10K 2020-2019.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return
    
    # Initialize detector
    detector = AITableDetector()
    
    # Detect tables
    try:
        detected_tables = detector.detect_tables_in_pdf(test_pdf)
        
        # Save results
        results_path = "output/detection/nvidia_2020-2019_ai_detection.json"
        detector.save_detection_results(detected_tables, results_path)
        
        # Get page ranges for LLMWhisperer
        page_ranges = detector.get_page_ranges_for_extraction(detected_tables)
        
        print("\n📋 Summary:")
        print("=" * 50)
        for stmt_type, pages in page_ranges.items():
            print(f"{stmt_type.value}: pages {pages}")
        
        print(f"\n💰 Cost savings: Instead of processing all ~100 pages, only process {sum(len(pages) for pages in page_ranges.values())} pages!")
        
    except Exception as e:
        print(f"❌ Error during detection: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()