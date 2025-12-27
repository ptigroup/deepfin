#!/usr/bin/env python3
"""Batch processor for all sample PDFs.

This script processes all PDFs in samples/input/ and generates a summary report.

Usage:
    python scripts/process_all.py
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from process_pdf_standalone import process_pdf_standalone


def process_all_samples(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict:
    """Process all sample PDFs and generate summary report.

    Args:
        input_dir: Directory containing sample PDFs
        output_dir: Directory for output files

    Returns:
        Summary report with processing results
    """
    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent
    if input_dir is None:
        input_dir = project_root / "samples" / "input"
    if output_dir is None:
        output_dir = project_root / "samples" / "output"

    print("\n" + "="*70)
    print("BATCH PROCESSING - Session 17.5 Validation")
    print("="*70 + "\n")

    # Find all PDFs
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"ERROR: No PDF files found in {input_dir}")
        return {"status": "error", "error": "No PDFs found"}

    print(f"Found {len(pdf_files)} PDF files to process:\n")
    for idx, pdf_path in enumerate(pdf_files, 1):
        size_kb = round(pdf_path.stat().st_size / 1024, 2)
        print(f"  {idx}. {pdf_path.name:<40} ({size_kb} KB)")

    print("\n" + "-"*70 + "\n")

    # Process each PDF
    results = []
    start_time = datetime.now()

    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_path.name}")
        print("-" * 70)

        try:
            result = process_pdf_standalone(
                pdf_path=pdf_path,
                output_dir=output_dir,
            )
            results.append(result)

        except KeyboardInterrupt:
            print("\n\nBatch processing interrupted by user")
            break
        except Exception as e:
            print(f"\nERROR: Failed to process {pdf_path.name}: {str(e)}")
            results.append({
                "status": "error",
                "pdf": pdf_path.name,
                "error": str(e),
            })
            continue

    # Generate summary report
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()

    successes = [r for r in results if r.get("status") == "success"]
    failures = [r for r in results if r.get("status") == "error"]

    print("\n\n" + "="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70 + "\n")

    print(f"Total PDFs:       {len(pdf_files)}")
    print(f"Processed:        {len(results)}")
    print(f"Successful:       {len(successes)}")
    print(f"Failed:           {len(failures)}")
    print(f"Total time:       {total_time:.2f} seconds")

    if successes:
        avg_time = sum(r["metadata"]["processing_time_seconds"] for r in successes) / len(successes)
        print(f"Average time:     {avg_time:.2f} seconds per PDF")

    # Success details
    if successes:
        print(f"\n{'SUCCESS Details:':<20}")
        print("-" * 70)
        for result in successes:
            meta = result["metadata"]
            print(f"  {meta['pdf_name']:<40}")
            print(f"    Type: {meta['document_type']:<25} Time: {meta['processing_time_seconds']:.2f}s")
            print(f"    Company: {meta['company_name']}")
            print(f"    Periods: {meta['periods_count']:<5} Line items: {meta['line_items_count']}")
            print()

    # Failure details
    if failures:
        print(f"\n{'FAILURE Details:':<20}")
        print("-" * 70)
        for result in failures:
            print(f"  {result['pdf']:<40}")
            print(f"    Error: {result['error']}")
            print()

    # Summary statistics
    if successes:
        print("\n" + "="*70)
        print("EXTRACTION STATISTICS")
        print("="*70 + "\n")

        doc_types = {}
        total_periods = 0
        total_line_items = 0

        for result in successes:
            meta = result["metadata"]
            doc_type = meta["document_type"]
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            total_periods += meta["periods_count"]
            total_line_items += meta["line_items_count"]

        print("Document types:")
        for doc_type, count in sorted(doc_types.items()):
            print(f"  - {doc_type:<30} {count} PDFs")

        print(f"\nTotal periods extracted:     {total_periods}")
        print(f"Total line items extracted:  {total_line_items}")

    print("\n" + "="*70)
    print(f"Batch processing {'COMPLETED' if not failures else 'COMPLETED WITH ERRORS'}")
    print("="*70 + "\n")

    return {
        "status": "success" if len(failures) == 0 else "partial",
        "total": len(pdf_files),
        "processed": len(results),
        "successes": len(successes),
        "failures": len(failures),
        "total_time_seconds": total_time,
        "results": results,
    }


def main():
    """Main entry point."""
    try:
        summary = process_all_samples()

        # Exit with appropriate code
        if summary["status"] == "success":
            sys.exit(0)
        elif summary["status"] == "partial":
            sys.exit(2)  # Partial success
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
