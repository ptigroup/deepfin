#!/usr/bin/env python3
"""
Hybrid PDF Processing Script - Session 17.5

Combines page detection (95% cost savings) with direct parsing (100% accuracy).

Pipeline:
1. PyMuPDF Page Detection (FREE, local) → Find relevant pages
2. LLMWhisperer Extraction → Targeted page extraction
3. Document Type Validation → Confidence scoring
4. Direct Parser → 100% accurate extraction
5. Schema Validation → Ensure correctness
6. Excel Export → Visual formatting with indentation

Usage:
    python scripts/process_pdf_hybrid.py path/to/document.pdf
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unstract.llmwhisperer import LLMWhispererClientV2
from app.extraction.page_detector import PageDetector, FinancialStatementType
from app.extraction.hybrid_pipeline import HybridExtractionPipeline

# Load environment variables
load_dotenv()

def process_pdf_with_hybrid_pipeline(pdf_path: str, output_dir: str = "output"):
    """
    Process a PDF through the complete hybrid extraction pipeline.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory for results

    Returns:
        Dictionary with extraction results
    """
    print(f"\n{'='*80}")
    print(f"HYBRID PDF PROCESSING - Session 17.5")
    print(f"{'='*80}\n")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_name = pdf_path.stem
    total_pages = 0

    # Get PDF page count
    import fitz
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)

    print(f"PDF: {pdf_name}")
    print(f"Total pages: {total_pages}\n")

    # ============================================================================
    # STEP 0: PAGE DETECTION (Cost Optimization)
    # ============================================================================
    print(f"{'='*80}")
    print("STEP 0: Page Detection (PyMuPDF - FREE)")
    print(f"{'='*80}\n")

    pages_to_extract = None
    detected_pages = {}

    if total_pages > 10:
        print("Large PDF detected - running intelligent page detection...")
        detector = PageDetector()

        try:
            detected_tables = detector.detect_financial_tables(str(pdf_path))

            if detected_tables and FinancialStatementType.INCOME_STATEMENT in detected_tables:
                primary_pages = detected_tables[FinancialStatementType.INCOME_STATEMENT]
                page_ranges = detector.get_page_ranges_for_extraction(detected_tables)
                pages_to_extract = page_ranges.get(FinancialStatementType.INCOME_STATEMENT)

                print(f"OK: DETECTED: Income statement on page(s) {primary_pages}")
                print(f"   Extracting pages: {pages_to_extract} (includes context)")

                cost_reduction = 100 - (len(pages_to_extract) / total_pages) * 100
                print(f"   Cost optimization: {cost_reduction:.1f}% reduction")
                print(f"   Characters to extract: ~{len(pages_to_extract) * 2000} (estimated)\n")

                detected_pages = detected_tables
            else:
                print("WARNING: No income statement detected - extracting full PDF\n")

        except Exception as e:
            print(f"WARNING: Page detection failed: {e}")
            print("   Falling back to full PDF extraction\n")
    else:
        print(f"Small PDF ({total_pages} pages) - skipping page detection\n")

    # ============================================================================
    # STEP 1: LLMWHISPERER EXTRACTION (Targeted)
    # ============================================================================
    print(f"{'='*80}")
    print("STEP 1: LLMWhisperer Extraction")
    print(f"{'='*80}\n")

    api_key = os.getenv("LLMWHISPERER_API_KEY")
    if not api_key:
        raise ValueError("LLMWHISPERER_API_KEY not found in environment")

    client = LLMWhispererClientV2(base_url="https://llmwhisperer-api.us-central.unstract.com/api/v2")

    whisper_params = {
        "file_path": str(pdf_path),
        "mode": "table",  # Changed from "form" - produces pipe-separated format for direct parser
        "output_mode": "layout_preserving",
        "wait_for_completion": True,
        "wait_timeout": 200,
    }

    # Add page filtering if detected
    if pages_to_extract:
        whisper_params["pages_to_extract"] = ",".join(map(str, pages_to_extract))
        print(f"Extracting pages: {pages_to_extract}")
    else:
        print(f"Extracting all {total_pages} pages")

    extraction_start = time.time()

    try:
        result = client.whisper(**whisper_params)

        # LLMWhisperer V2 response format: result["extraction"]["result_text"]
        extraction = result.get("extraction", {})
        raw_text = extraction.get("result_text", "")

        if not raw_text:
            raise ValueError("No text extracted from PDF")

        extraction_time = time.time() - extraction_start

        print(f"\nOK: Extraction complete:")
        print(f"   Characters extracted: {len(raw_text):,}")
        print(f"   Extraction time: {extraction_time:.1f}s")

        # Cost estimation (approximate)
        cost_per_1k_chars = 0.023  # GPT-4o-mini input cost
        estimated_cost = (len(raw_text) / 1000) * cost_per_1k_chars
        print(f"   Estimated API cost: ${estimated_cost:.2f}\n")

    except Exception as e:
        print(f"\nERROR: Extraction failed: {e}\n")
        raise

    # ============================================================================
    # STEP 2-7: HYBRID PIPELINE (Detection, Parsing, Validation, Export)
    # ============================================================================
    print(f"{'='*80}")
    print("STEP 2-7: Hybrid Extraction Pipeline")
    print(f"{'='*80}\n")

    pipeline = HybridExtractionPipeline(output_dir=output_dir)

    try:
        pipeline_start = time.time()

        result = pipeline.extract_with_hybrid_pipeline(
            pdf_path=str(pdf_path),
            raw_text=raw_text,
            pages_extracted=pages_to_extract if pages_to_extract else list(range(1, total_pages + 1))
        )

        pipeline_time = time.time() - pipeline_start

        print(f"\nOK: Hybrid pipeline complete:")
        print(f"   Processing time: {pipeline_time:.1f}s")
        print(f"   Total time: {extraction_time + pipeline_time:.1f}s\n")

        return result

    except Exception as e:
        print(f"\nERROR: Pipeline failed: {e}\n")
        raise


def print_results(result: dict):
    """Print formatted extraction results."""
    print(f"\n{'='*80}")
    print("EXTRACTION RESULTS")
    print(f"{'='*80}\n")

    print(f"Document Information:")
    print(f"   PDF: {result['pdf_name']}")
    print(f"   Type: {result['document_type']}")
    print(f"   Detection Confidence: {result['confidence']:.2%}")
    print(f"   Pages Extracted: {result['pages_extracted']}\n")

    print(f"Extraction Methods:")
    direct = result['direct_parser']
    print(f"   Direct Parser: {'SUCCESS' if direct['success'] else 'FAILED'}")
    if direct['success']:
        print(f"      Line items: {direct['line_items_count']}")
        print(f"      Processing time: {direct['extraction_time']:.2f}s")
    else:
        print(f"      Error: {direct.get('error', 'Unknown')}")

    pydantic = result['pydantic_ai']
    print(f"   Pydantic AI: {'SUCCESS' if pydantic['success'] else 'SKIPPED'}")
    if pydantic.get('error'):
        print(f"      Note: {pydantic['error']}\n")

    print(f"Validation Report:")
    validation = result['validation_report']
    print(f"   Accuracy: {validation['accuracy_score']:.1%}")
    print(f"   Discrepancies: {validation['discrepancies_count']}")
    print(f"   Recommendation: {validation['recommendation']}\n")

    print(f"Output Files:")
    for file_type, path in result['output_paths'].items():
        print(f"   {file_type.upper()}: {path}")

    # Show run information
    print(f"\nRun Information:")
    print(f"   Run ID: {result.get('run_id', 'N/A')}")
    print(f"   Run Directory: {result.get('run_dir', 'N/A')}")

    print(f"\n{'='*80}")
    print(f"FINAL ACCURACY: {result['accuracy']:.1%}")
    print(f"{'='*80}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/process_pdf_hybrid.py <pdf_path>")
        print("\nExample:")
        print('  python scripts/process_pdf_hybrid.py "samples/input/NVIDIA 10K 2020-2019.pdf"')
        sys.exit(1)

    pdf_path = sys.argv[1]

    try:
        start_time = time.time()

        result = process_pdf_with_hybrid_pipeline(pdf_path)
        print_results(result)

        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.1f}s\n")

        print("Processing complete!")

    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
