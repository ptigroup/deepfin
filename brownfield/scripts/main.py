#!/usr/bin/env python3
"""
Main Financial Document Processing Pipeline Orchestrator

This is the main entry point that coordinates the entire modular pipeline:
01_read_input.py → 02_detect_tables.py → 03_extract_tables.py → 04_process_all_pdfs.py → 05_merge_excel_files.py

Usage: python3 main.py
"""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import core infrastructure first
from core import PATHS, ensure_project_context

# Suppress LLMWhisperer DEBUG logging in production mode (early suppression)
if os.getenv('MODE', 'production').lower() == 'production':
    logging.getLogger('unstract.llmwhisperer.client_v2').setLevel(logging.CRITICAL)
    logging.getLogger('unstract.llmwhisperer').setLevel(logging.CRITICAL)
    logging.getLogger('unstract').setLevel(logging.CRITICAL)

# Import modular pipeline components
from pipeline_01_input_discovery.pipeline_01_read_input import InputReader
from pipeline_02_table_detection.pipeline_02_detect_tables import TableDetector
from pipeline_03_extraction.pipeline_03_extract_tables import TableExtractor
from pipeline_04_processing.pipeline_04_process_all_pdfs import PDFProcessor
from pipeline_05_consolidation.pipeline_05_merge_excel_files import ExcelMerger

# Import enterprise output manager and logging
from core.pipeline_01_2_enterprise_manager import EnterpriseOutputManager
from core.pipeline_logger import logger

def create_output_folders():
    """Create output folder structure using centralized path management."""
    PATHS.output_dir.mkdir(parents=True, exist_ok=True)

def main():
    """Main pipeline orchestrator."""
    load_dotenv()
    
    # Ensure safe project context and paths
    ensure_project_context()
    
    logger.debug("🚀 Financial Document Processing Pipeline")
    logger.debug("=" * 60)
    logger.debug("Modular Pipeline: 01→02→03→04→05")
    logger.debug("Cost-Optimized: AI Detection + Targeted LLMWhisperer Extraction")
    
    # Initialize enterprise output manager
    mode = os.getenv('MODE', 'production').lower()
    output_manager = EnterpriseOutputManager(mode=mode)
    
    # Create output folders
    create_output_folders()
    
    # Initialize pipeline components
    input_reader = InputReader()
    table_detector = TableDetector()
    table_extractor = TableExtractor()
    pdf_processor = PDFProcessor()
    # ExcelMerger will be initialized later with the run directory
    
    try:
        # Step 1: Read input folder and get all PDFs
        logger.global_progress.update_stage('input_discovery', 0, "Scanning input folder")
        pdf_files = input_reader.scan_input_folder("input")
        
        if not pdf_files:
            logger.error("No PDF files found in input folder")
            return
        
        logger.global_progress.update_stage('input_discovery', 100, f"Found {len(pdf_files)} PDF files")
        logger.debug(f"✅ Found {len(pdf_files)} PDF files to process")
        
        # Start enterprise run tracking
        run_id = output_manager.start_run(
            input_files=[str(f) for f in pdf_files],
            processing_mode="multi_pdf_consolidation"
        )
        
        # Step 2-4: Process each PDF (detect, extract, consolidate)
        logger.debug("🚀 Step 2-4: PDF Processing")
        logger.debug("=" * 60)
        processed_files = []
        stage_start_time = time.time()
        
        for i, pdf_path in enumerate(pdf_files, 1):
            # Determine stage key based on PDF index
            stage_key = 'pdf1_processing' if i == 1 else 'pdf2_processing'
            pdf_name = Path(pdf_path).name
            
            try:
                # AI table detection (Step 2)
                logger.global_progress.update_stage(stage_key, 10, f"AI detecting tables in {pdf_name}")
                detection_start = time.time()
                detected_tables = table_detector.detect_financial_tables(pdf_path)
                detection_time = time.time() - detection_start
                
                if not detected_tables:
                    logger.warning(f"No financial tables detected in {pdf_name}")
                    continue
                
                # Targeted LLMWhisperer extraction (Step 3) 
                logger.global_progress.update_stage(stage_key, 40, f"Extracting {len(detected_tables)} tables with LLMWhisperer")
                extraction_start = time.time()
                # Use enterprise run directory for output
                run_output_dir = output_manager.current_run_dir
                consolidated_excel = table_extractor.extract_to_consolidated_excel(
                    pdf_path, detected_tables, str(run_output_dir)
                )
                extraction_time = time.time() - extraction_start
                
                if consolidated_excel:
                    logger.global_progress.update_stage(stage_key, 90, "Creating Excel files")
                    # Register files with output manager
                    output_manager.register_file(str(consolidated_excel), "final_excel", "extraction", {
                        "pdf_source": str(pdf_path),
                        "tables_detected": len(detected_tables),
                        "detection_time": detection_time,
                        "extraction_time": extraction_time
                    })
                    
                    # Create proper PDFProcessingResult object for Pipeline 05
                    from pipeline_04_processing.pipeline_04_process_all_pdfs import PDFProcessingResult
                    result = PDFProcessingResult(pdf_path)
                    result.excel_path = consolidated_excel
                    result.detected_tables = detected_tables
                    result.processing_success = True
                    processed_files.append(result)
                    
                    logger.global_progress.update_stage(stage_key, 100, f"Completed {len(detected_tables)} Excel files")
                    logger.debug(f"✅ Created {len(detected_tables)} Excel files for {pdf_name}")
                else:
                    logger.error(f"Failed to extract: {pdf_name}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_name}: {e}")
                continue
        
        # Log extraction stage completion
        extraction_duration = time.time() - stage_start_time
        output_manager.log_stage_completion("pdf_extraction", extraction_duration, 
                                           [result.excel_path for result in processed_files])
        
        # Step 5: Use multi-PDF consolidated files as final results (skip redundant merger)
        if processed_files:
            logger.debug("🚀 Step 5: Final Consolidation")
            logger.debug("=" * 60)
            logger.global_progress.update_stage('consolidation', 10, "Scanning for consolidated files")
            merge_start = time.time()
            
            # Find all relevant Excel files for final output (both consolidated and individual)
            import glob
            # Search for multi-PDF consolidated files (stage 07) with numerical prefixes
            consolidated_pattern = f"{output_manager.current_run_dir}/*_07_excel_multi_pdf_consolidated_*.xlsx"
            consolidated_files = glob.glob(consolidated_pattern)
            
            # Search for individual shareholders equity files (stage 03) with numerical prefixes
            individual_pattern = f"{output_manager.current_run_dir}/05_shareholders_equity_*_03_excel.xlsx"
            individual_files = glob.glob(individual_pattern)
            
            all_relevant_files = consolidated_files + individual_files
            
            if all_relevant_files:
                # Prepare final files dictionary with 6 statement types
                final_files = {}
                
                # Process multi-PDF consolidated files with numerical prefixes
                for file_path in consolidated_files:
                    file_name = Path(file_path).name
                    # New format: 01_income_statement_07_excel_multi_pdf_consolidated_period.xlsx
                    if file_name.startswith("01_income_statement_"):
                        final_files["income_statement"] = file_path
                    elif file_name.startswith("03_balance_sheet_"):
                        final_files["balance_sheet"] = file_path
                    elif file_name.startswith("04_cash_flow_"):
                        final_files["cash_flow"] = file_path
                    elif file_name.startswith("02_comprehensive_income_"):
                        final_files["comprehensive_income"] = file_path
                
                # Process individual shareholders equity files with numerical prefixes
                for file_path in individual_files:
                    file_name = Path(file_path).name
                    # New format: 05_shareholders_equity_ANYPDFNAME_03_excel.xlsx
                    if file_name.startswith("05_shareholders_equity_"):
                        # Extract PDF source name dynamically (everything between 05_shareholders_equity_ and _03_excel)
                        # Remove the extension first
                        name_without_ext = file_name.replace('.xlsx', '')
                        
                        # Find the pattern: 05_shareholders_equity_[PDFNAME]_03_excel
                        if '_03_excel' in name_without_ext:
                            # Split on _03_excel to get the PDF name part
                            pdf_part = name_without_ext.split('_03_excel')[0]
                            # Remove the "05_shareholders_equity_" prefix
                            pdf_name = pdf_part.replace('05_shareholders_equity_', '', 1)
                            key = f"shareholders_equity_{pdf_name}"
                            final_files[key] = file_path
                
                # Initialize ExcelMerger with run directory
                excel_merger = ExcelMerger(output_folder=output_manager.current_run_dir)
                
                # Use new direct worksheet copying method to preserve original formatting
                logger.global_progress.update_stage('consolidation', 50, f"Merging {len(final_files)} Excel files")
                logger.debug(f"Processing {len(final_files)} Excel files (4 consolidated + {len(individual_files)} individual):")
                for stmt_type, file_path in final_files.items():
                    logger.debug(f"  • {stmt_type}: {Path(file_path).name}")
                
                try:
                    logger.global_progress.update_stage('consolidation', 80, "Creating final workbook")
                    final_combined_excel = excel_merger.merge_consolidated_excel_files(final_files)
                    if final_combined_excel:
                        # File is already in the run directory
                        final_files["combined_workbook"] = final_combined_excel
                        logger.global_progress.update_stage('final_output', 100, f"Created {Path(final_combined_excel).name}")
                        logger.debug(f"✅ Created {Path(final_combined_excel).name}")
                    else:
                        logger.warning("Could not create final consolidated Excel")
                except Exception as e:
                    logger.error(f"Error creating combined Excel: {e}")
                    logger.debug_detailed(f"Full traceback: {e}")
                
                merge_duration = time.time() - merge_start
                # Log organization stage completion
                output_manager.log_stage_completion("excel_organization", merge_duration, list(final_files.values()))
                
                # Complete the run successfully
                run_dir = output_manager.complete_run(final_files, success=True)
                total_duration = time.time() - stage_start_time
                
                # Complete the global progress
                logger.global_progress.complete(f"Pipeline completed in {total_duration:.0f}s")
                
                # Show final output location (the only essential info)
                try:
                    relative_path = Path(run_dir).relative_to(Path.cwd())
                    print(f"📁 Output: {relative_path}")
                except ValueError:
                    # Fallback to absolute path if relative path fails
                    print(f"📁 Output: {run_dir}")
                
                # Debug information (hidden in production)
                logger.debug(f"✅ Final Consolidated Files: {len(final_files)} statement types")
                for stmt_type, file_path in final_files.items():
                    logger.debug(f"  • {stmt_type}: {Path(file_path).name}")
                logger.debug(f"ℹ️  Individual Excel Files: {len(processed_files)} PDFs processed")
                logger.debug(f"ℹ️  Cost Savings: AI detection + targeted extraction")
                logger.debug(f"Enterprise Run: {run_id}")
                logger.debug(f"Run Directory: {Path(run_dir).name}")
                
                for file_info in processed_files:
                    tables_count = len(file_info.detected_tables)
                    logger.debug(f"  • {Path(file_info.pdf_path).name}: {tables_count} tables detected")
                
            else:
                logger.error("No consolidated Excel files found")
                output_manager.complete_run({}, success=False)
        else:
            logger.error("No PDFs were successfully processed")
            output_manager.complete_run({}, success=False)
            
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        logger.debug_detailed(f"Full traceback: {e}")
        
        # Complete run as failed
        if 'output_manager' in locals():
            output_manager.complete_run({}, success=False)
        
        sys.exit(1)

if __name__ == "__main__":
    main()