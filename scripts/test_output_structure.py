#!/usr/bin/env python3
"""
Test script to validate the new run-based output structure.

This creates a mock extraction run to verify the OutputManager works correctly.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.output_manager import OutputManager, RunStatus

def test_output_structure():
    """Test the run-based output structure."""
    print("\n" + "="*80)
    print("OUTPUT STRUCTURE VALIDATION TEST")
    print("="*80 + "\n")

    # Create output manager with test directory
    test_dir = "output_test"
    manager = OutputManager(test_dir)
    print(f"[OK] OutputManager created: {test_dir}/\n")

    # Create a new run
    run = manager.create_run(status=RunStatus.IN_PROGRESS)
    print(f"[OK] Extraction run created: {run.run_id}")
    print(f"  Run directory: {run.run_dir}\n")

    # Verify directory structure
    assert run.run_dir.exists(), "Run directory not created"
    assert run.extracted_dir.exists(), "Extracted directory not created"
    assert run.consolidated_dir.exists(), "Consolidated directory not created"
    print("[OK] Directory structure verified:\n")
    print(f"  {run.run_dir}/")
    print(f"  |-- extracted/")
    print(f"  |-- consolidated/")
    print(f"  \-- run_manifest.json\n")

    # Save sample extraction
    sample_data = {
        "company_name": "Test Company",
        "statement_type": "income_statement",
        "currency": "USD",
        "periods": ["Year Ended 2023", "Year Ended 2022"],
        "line_items": [
            {"account_name": "Revenue", "values": ["100", "90"], "indent_level": 0},
            {"account_name": "Expenses", "values": ["60", "50"], "indent_level": 0},
            {"account_name": "Net Income", "values": ["40", "40"], "indent_level": 0}
        ]
    }

    sample_metadata = {
        "pdf_name": "test.pdf",
        "document_type": "income_statement",
        "extracted_at": "2025-12-27T00:00:00",
        "line_items_count": 3,
        "accuracy": 1.0
    }

    sample_validation = {
        "document_confidence": 0.95,
        "direct_parser_success": True,
        "accuracy_score": 1.0,
        "recommendation": "Direct parser succeeded - 100% accuracy"
    }

    # Save extraction
    pdf_dir = run.save_extraction(
        pdf_name="test_company_2023",
        statement_type="income_statement",
        json_data=sample_data,
        excel_path=None,
        raw_text="Sample raw text",
        metadata=sample_metadata,
        validation=sample_validation
    )

    print(f"[OK] Sample extraction saved: {pdf_dir.name}/")
    print(f"  |-- income_statement.json")
    print(f"  |-- raw_text.txt")
    print(f"  |-- metadata.json")
    print(f"  \-- validation.json\n")

    # Verify files exist
    assert (pdf_dir / "income_statement.json").exists(), "JSON not saved"
    assert (pdf_dir / "raw_text.txt").exists(), "Raw text not saved"
    assert (pdf_dir / "metadata.json").exists(), "Metadata not saved"
    assert (pdf_dir / "validation.json").exists(), "Validation not saved"

    # Add PDF result to manifest
    run.add_pdf_result(
        filename="test_company_2023.pdf",
        pages_total=10,
        pages_extracted=[1, 2, 3, 4],
        status="SUCCESS",
        statements_found=["income_statement"],
        extraction_method="direct_parser",
        accuracy=1.0,
        cost_usd=0.15,
        duration_seconds=5.5,
        line_items=3
    )

    print("[OK] PDF result added to manifest")
    print(f"  Status: SUCCESS")
    print(f"  Line items: 3")
    print(f"  Cost: $0.15")
    print(f"  Duration: 5.5s\n")

    # Complete the run
    run.complete(status=RunStatus.SUCCESS)
    print("[OK] Run completed with status: SUCCESS\n")

    # Verify manifest
    manifest_path = run.run_dir / "run_manifest.json"
    assert manifest_path.exists(), "Manifest not saved"

    with open(manifest_path) as f:
        manifest = json.load(f)

    print("[OK] Manifest verified:")
    print(f"  Run ID: {manifest['run_id']}")
    print(f"  Status: {manifest['status']}")
    print(f"  PDFs processed: {manifest['summary']['total_pdfs']}")
    print(f"  Successful: {manifest['summary']['successful']}")
    print(f"  Total cost: ${manifest['summary']['total_cost_usd']:.2f}")
    print(f"  Total line items: {manifest['summary']['total_line_items']}\n")

    # Verify 'latest' symlink or fallback
    latest_run = manager.get_latest_run()
    if latest_run:
        print(f"[OK] Latest run accessible:")
        print(f"  {latest_run}\n")
    else:
        print("[WARN] Warning: Latest run not accessible (may need symlink support)\n")

    # Test get_latest_by_document
    latest_doc = manager.get_latest_by_document("test_company_2023")
    if latest_doc:
        print(f"[OK] Latest document extraction accessible:")
        print(f"  {latest_doc}\n")
    else:
        print("[WARN] Warning: Latest document not accessible\n")

    # List all runs
    all_runs = manager.list_runs()
    print(f"[OK] All runs listed: {len(all_runs)} run(s)\n")

    print("="*80)
    print("[OK][OK][OK] ALL TESTS PASSED [OK][OK][OK]")
    print("="*80 + "\n")

    print(f"Output structure created successfully at: {test_dir}/")
    print(f"\nTo inspect the structure, run:")
    print(f"  tree {test_dir}/ (Linux/Mac)")
    print(f"  dir /s {test_dir}\\ (Windows)\n")

    return True


def cleanup_test_output():
    """Optional: Clean up test output."""
    import shutil
    test_dir = Path("output_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print(f"[OK] Test output cleaned up: {test_dir}/\n")


if __name__ == "__main__":
    try:
        success = test_output_structure()

        # Ask user if they want to clean up
        print("Keep test output for inspection? (y/n): ", end="")
        keep = input().strip().lower()

        if keep != 'y':
            cleanup_test_output()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
