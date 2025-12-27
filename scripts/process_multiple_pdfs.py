#!/usr/bin/env python3
"""
Multi-PDF Processing Script - Session 17.5

Process multiple PDFs in a SINGLE run with automatic consolidation.

Pipeline:
1. Page Detection (PyMuPDF) → Find relevant pages for each PDF
2. LLMWhisperer Extraction → Targeted extraction
3. Document Type Validation → Confidence scoring
4. Direct Parser → 100% accurate extraction
5. Auto-consolidation → Merge same statement types
6. Output → JSON + Excel (per-PDF + consolidated)

Usage:
    python scripts/process_multiple_pdfs.py PDF1.pdf PDF2.pdf [PDF3.pdf ...]

Example:
    python scripts/process_multiple_pdfs.py \\
        "samples/input/NVIDIA 10K 2020-2019.pdf" \\
        "samples/input/NVIDIA 10K 2022-2021.pdf"
"""

import os
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unstract.llmwhisperer import LLMWhispererClientV2
from app.extraction.page_detector import PageDetector, FinancialStatementType
from app.extraction.hybrid_pipeline import HybridExtractionPipeline
from app.core.output_manager import OutputManager, ExtractionRun, RunStatus
from scripts.consolidate_hybrid_outputs import HybridOutputConsolidator, create_schema_from_consolidated
from app.export.excel_exporter import SchemaBasedExcelExporter

# Load environment variables
load_dotenv()


def process_multiple_pdfs(pdf_paths: List[str], output_dir: str = "output"):
    """
    Process multiple PDFs in a single run with automatic consolidation.

    Args:
        pdf_paths: List of PDF file paths
        output_dir: Base output directory (default: "output")

    Returns:
        Dictionary with run information and results
    """
    print(f"\n{'='*80}")
    print(f"MULTI-PDF PROCESSING - Session 17.5")
    print(f"{'='*80}\n")

    print(f"Processing {len(pdf_paths)} PDFs in ONE run")
    print(f"Output directory: {output_dir}\n")

    # Create output manager and run
    output_manager = OutputManager(output_dir)
    run = output_manager.create_run(status=RunStatus.IN_PROGRESS)

    print(f"Created run: {run.run_id}\n")

    # Initialize LLMWhisperer client
    api_key = os.getenv("LLMWHISPERER_API_KEY")
    if not api_key:
        raise ValueError("LLMWHISPERER_API_KEY not found in environment")

    client = LLMWhispererClientV2(base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2")
    page_detector = PageDetector()

    # Track results by statement type for consolidation
    extraction_results = []
    results_by_statement_type = defaultdict(list)

    total_start_time = time.time()

    # Process each PDF
    for i, pdf_path in enumerate(pdf_paths, 1):
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"ERROR: PDF not found: {pdf_path}")
            continue

        pdf_name = pdf_path.stem
        print(f"{'='*80}")
        print(f"PDF {i}/{len(pdf_paths)}: {pdf_name}")
        print(f"{'='*80}\n")

        try:
            # Get PDF page count
            import fitz
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)

            print(f"Total pages: {total_pages}")

            # STEP 1: Page Detection
            pages_to_extract = None
            if total_pages > 10:
                print(f"Running page detection...")
                try:
                    detected_tables = page_detector.detect_financial_tables(str(pdf_path))

                    if detected_tables and FinancialStatementType.INCOME_STATEMENT in detected_tables:
                        page_ranges = page_detector.get_page_ranges_for_extraction(detected_tables)
                        pages_to_extract = page_ranges.get(FinancialStatementType.INCOME_STATEMENT)
                        print(f"  Detected pages: {pages_to_extract}")
                        cost_reduction = 100 - (len(pages_to_extract) / total_pages) * 100
                        print(f"  Cost reduction: {cost_reduction:.1f}%\n")
                except Exception as e:
                    print(f"  Page detection failed: {e}")
                    print(f"  Falling back to full PDF\n")

            # STEP 2: LLMWhisperer Extraction
            print(f"Extracting text...")
            whisper_params = {
                "file_path": str(pdf_path),
                "mode": "table",
                "output_mode": "layout_preserving",
                "wait_for_completion": True,
                "wait_timeout": 200,
            }

            if pages_to_extract:
                whisper_params["pages_to_extract"] = ",".join(map(str, pages_to_extract))

            extraction_start = time.time()
            result = client.whisper(**whisper_params)
            extraction = result.get("extraction", {})
            raw_text = extraction.get("result_text", "")
            extraction_time = time.time() - extraction_start

            print(f"  Extracted {len(raw_text):,} characters in {extraction_time:.1f}s\n")

            # STEP 3-7: Hybrid Pipeline (Detection, Parsing, Validation, Export)
            print(f"Running hybrid extraction pipeline...")
            pipeline = HybridExtractionPipeline(output_dir=output_dir)
            pipeline.current_run = run  # Use our shared run

            pipeline_start = time.time()
            extraction_result = pipeline.extract_with_hybrid_pipeline(
                pdf_path=str(pdf_path),
                raw_text=raw_text,
                pages_extracted=pages_to_extract if pages_to_extract else list(range(1, total_pages + 1))
            )
            pipeline_time = time.time() - pipeline_start

            print(f"  Pipeline complete in {pipeline_time:.1f}s")
            print(f"  Document type: {extraction_result['document_type']}")
            print(f"  Accuracy: {extraction_result['accuracy']:.1%}\n")

            # Track result for consolidation
            extraction_results.append(extraction_result)
            results_by_statement_type[extraction_result['document_type']].append({
                "pdf_name": pdf_name,
                "result": extraction_result
            })

        except Exception as e:
            print(f"  ERROR processing {pdf_name}: {e}\n")
            import traceback
            traceback.print_exc()
            continue

    # STEP 8: Auto-consolidation
    print(f"\n{'='*80}")
    print(f"AUTO-CONSOLIDATION")
    print(f"{'='*80}\n")

    consolidated_count = 0
    for statement_type, pdfs in results_by_statement_type.items():
        if len(pdfs) < 2:
            print(f"{statement_type}: Only 1 PDF, skipping consolidation")
            continue

        print(f"\n{statement_type}: Consolidating {len(pdfs)} PDFs...")

        try:
            # Collect JSON paths from this run
            json_paths = []
            for pdf_info in pdfs:
                json_path = pdf_info["result"]["output_paths"]["json"]
                json_paths.append(json_path)

            # Consolidate
            consolidator = HybridOutputConsolidator()
            consolidated_data = consolidator.consolidate_json_files(json_paths)

            # Create schema and export to Excel
            schema = create_schema_from_consolidated(consolidated_data)
            exporter = SchemaBasedExcelExporter()

            # Save consolidated outputs using OutputManager
            # Extract years from periods
            periods = consolidated_data["reporting_periods"]
            years = []
            for period in periods:
                import re
                year_match = re.search(r'(\d{4})', period)
                if year_match:
                    years.append(year_match.group(1))

            # Save consolidated JSON
            year_range = f"{years[0]}-{years[-1]}" if len(years) > 1 else years[0]
            consolidated_json_filename = f"{statement_type}_{year_range}.json"
            consolidated_excel_filename = f"{statement_type}_{year_range}.xlsx"

            # Create temp Excel file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.xlsx') as tmp:
                excel_temp_path = tmp.name

            exporter.export_to_excel(schema, excel_temp_path)

            # Save using OutputManager
            consolidated_dir = run.save_consolidated(
                statement_type=statement_type,
                years=years,
                json_data=consolidated_data,
                excel_path=excel_temp_path,
                source_count=len(pdfs),
                line_items=len(consolidated_data["data"]["line_items"])
            )

            # Clean up temp file
            os.remove(excel_temp_path)

            print(f"  ✓ Consolidated: {consolidated_json_filename}")
            print(f"  ✓ Excel: {consolidated_excel_filename}")
            print(f"  ✓ Saved to: {consolidated_dir}")

            consolidated_count += 1

        except Exception as e:
            print(f"  ERROR consolidating {statement_type}: {e}")
            import traceback
            traceback.print_exc()

    # Complete the run
    total_time = time.time() - total_start_time

    successful = sum(1 for r in extraction_results if r.get('accuracy', 0) >= 0.7)
    failed = len(extraction_results) - successful

    if failed == 0:
        run_status = RunStatus.SUCCESS
    elif successful > 0:
        run_status = RunStatus.PARTIAL
    else:
        run_status = RunStatus.FAILED

    run.complete(status=run_status)

    # Print summary
    print(f"\n{'='*80}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*80}\n")

    print(f"Run: {run.run_id} ({run_status})")
    print(f"Total time: {total_time:.1f}s")
    print(f"PDFs processed: {len(extraction_results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"Consolidations: {consolidated_count}")
    print(f"\nOutput directory: {run.run_dir}")
    print(f"Latest run: {output_dir}/runs/latest\n")

    return {
        "run_id": run.run_id,
        "run_dir": str(run.run_dir),
        "status": run_status,
        "total_time": total_time,
        "pdfs_processed": len(extraction_results),
        "successful": successful,
        "failed": failed,
        "consolidations": consolidated_count
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/process_multiple_pdfs.py PDF1.pdf PDF2.pdf [PDF3.pdf ...]")
        print("\nExample:")
        print('  python scripts/process_multiple_pdfs.py \\')
        print('    "samples/input/NVIDIA 10K 2020-2019.pdf" \\')
        print('    "samples/input/NVIDIA 10K 2022-2021.pdf"')
        sys.exit(1)

    pdf_paths = sys.argv[1:]

    try:
        result = process_multiple_pdfs(pdf_paths)
        sys.exit(0 if result["status"] == RunStatus.SUCCESS else 1)

    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
