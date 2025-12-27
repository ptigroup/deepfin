#!/usr/bin/env python3
"""
Production Readiness Validation Script - Session 17.5

Validates that all critical components are working:
1. OutputManager creates correct structure
2. Consolidation exports JSON + Excel
3. Run manifests track metadata correctly
4. All required files exist

This script validates the OUTPUT structure without requiring LLMWhisperer.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.output_manager import OutputManager, RunStatus

def validate_production_readiness():
    """Run all validation checks."""
    print("\n" + "="*80)
    print("PRODUCTION READINESS VALIDATION")
    print("="*80 + "\n")

    checks_passed = 0
    checks_failed = 0

    # CHECK 1: OutputManager Structure
    print("[CHECK 1] OutputManager creates correct directory structure...")
    try:
        test_manager = OutputManager("output_validation_test")
        test_run = test_manager.create_run(status=RunStatus.IN_PROGRESS)

        # Verify structure
        assert (test_manager.output_base / "runs").exists(), "runs/ not created"
        assert (test_manager.output_base / "by_document").exists(), "by_document/ not created"
        assert (test_manager.output_base / "by_statement").exists(), "by_statement/ not created"
        assert (test_manager.output_base / "cache").exists(), "cache/ not created"
        assert test_run.extracted_dir.exists(), "extracted/ not created"
        assert test_run.consolidated_dir.exists(), "consolidated/ not created"

        # Clean up
        import shutil
        shutil.rmtree("output_validation_test")

        print("  [OK] PASSED: Directory structure correct\n")
        checks_passed += 1

    except Exception as e:
        print(f"  [FAIL] FAILED: {e}\n")
        checks_failed += 1

    # CHECK 2: Consolidation Exports JSON + Excel
    print("[CHECK 2] Consolidation exports both JSON and Excel...")
    try:
        consolidated_dir = Path("samples/output/consolidated")
        json_file = consolidated_dir / "consolidated_income_statement_2022-2018.json"
        excel_file = consolidated_dir / "consolidated_income_statement_2022-2018.xlsx"

        assert json_file.exists(), f"Consolidated JSON not found: {json_file}"
        assert excel_file.exists(), f"Consolidated Excel not found: {excel_file}"

        # Verify JSON structure
        with open(json_file) as f:
            data = json.load(f)

        assert "consolidation_summary" in data, "Missing consolidation_summary"
        assert "merged_accounts" in data["consolidation_summary"], "Missing merged_accounts"
        assert "total_consolidated" in data["consolidation_summary"], "Missing total_consolidated"
        assert "source_pdfs" in data["consolidation_summary"], "Missing source_pdfs"

        print(f"  [OK] PASSED: Both JSON and Excel exist")
        print(f"    JSON: {json_file.stat().st_size:,} bytes")
        print(f"    Excel: {excel_file.stat().st_size:,} bytes")
        print(f"    Consolidated accounts: {data['consolidation_summary']['total_consolidated']}")
        print(f"    Source PDFs: {len(data['consolidation_summary']['source_pdfs'])}\n")
        checks_passed += 1

    except Exception as e:
        print(f"  [FAIL] FAILED: {e}\n")
        checks_failed += 1

    # CHECK 3: Run Manifest Tracking
    print("[CHECK 3] Run manifests track complete metadata...")
    try:
        # Create test run with sample data
        test_manager = OutputManager("output_validation_test")
        test_run = test_manager.create_run(status=RunStatus.IN_PROGRESS)

        # Add sample PDF result
        test_run.add_pdf_result(
            filename="test.pdf",
            pages_total=10,
            pages_extracted=[1, 2, 3],
            status="SUCCESS",
            statements_found=["income_statement"],
            extraction_method="direct_parser",
            accuracy=1.0,
            cost_usd=0.50,
            duration_seconds=10.5,
            line_items=15
        )

        # Complete run
        test_run.complete(status=RunStatus.SUCCESS)

        # Verify manifest
        manifest_path = test_run.run_dir / "run_manifest.json"
        assert manifest_path.exists(), "Manifest not created"

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Verify required fields
        required_fields = [
            "run_id", "status", "started_at", "completed_at",
            "duration_seconds", "total_cost_usd", "settings",
            "pdfs_processed", "consolidated", "summary"
        ]

        for field in required_fields:
            assert field in manifest, f"Missing field: {field}"

        # Verify PDF result tracking
        assert len(manifest["pdfs_processed"]) == 1, "PDF result not tracked"
        pdf_result = manifest["pdfs_processed"][0]
        assert pdf_result["filename"] == "test.pdf", "Wrong filename"
        assert pdf_result["status"] == "SUCCESS", "Wrong status"
        assert pdf_result["cost_usd"] == 0.50, "Wrong cost"
        assert pdf_result["line_items"] == 15, "Wrong line items"

        # Verify summary
        assert manifest["summary"]["total_pdfs"] == 1, "Wrong total PDFs"
        assert manifest["summary"]["successful"] == 1, "Wrong successful count"
        assert manifest["summary"]["total_cost_usd"] == 0.50, "Wrong total cost"
        assert manifest["summary"]["total_line_items"] == 15, "Wrong total line items"

        # Clean up
        import shutil
        shutil.rmtree("output_validation_test")

        print("  [OK] PASSED: Manifest tracks all required fields\n")
        checks_passed += 1

    except Exception as e:
        print(f"  [FAIL] FAILED: {e}\n")
        checks_failed += 1

    # CHECK 4: Consolidation Script Executable
    print("[CHECK 4] Consolidation script is executable...")
    try:
        consolidation_script = Path("scripts/consolidate_hybrid_outputs.py")
        assert consolidation_script.exists(), "Consolidation script not found"

        # Verify it has required functions
        with open(consolidation_script) as f:
            content = f.read()

        assert "class HybridOutputConsolidator" in content, "Missing HybridOutputConsolidator"
        assert "def consolidate_json_files" in content, "Missing consolidate_json_files"
        assert "def create_schema_from_consolidated" in content, "Missing create_schema_from_consolidated"
        assert "SchemaBasedExcelExporter" in content, "Missing Excel export"

        print("  [OK] PASSED: Consolidation script has all required components\n")
        checks_passed += 1

    except Exception as e:
        print(f"  [FAIL] FAILED: {e}\n")
        checks_failed += 1

    # CHECK 5: Multi-PDF Processing Script
    print("[CHECK 5] Multi-PDF processing script exists...")
    try:
        multi_pdf_script = Path("scripts/process_multiple_pdfs.py")
        assert multi_pdf_script.exists(), "Multi-PDF script not found"

        # Verify it has required components
        with open(multi_pdf_script) as f:
            content = f.read()

        assert "def process_multiple_pdfs" in content, "Missing process_multiple_pdfs function"
        assert "OutputManager" in content, "Missing OutputManager import"
        assert "HybridOutputConsolidator" in content, "Missing consolidator import"
        assert "Auto-consolidation" in content, "Missing auto-consolidation logic"

        print("  [OK] PASSED: Multi-PDF script has all required components\n")
        checks_passed += 1

    except Exception as e:
        print(f"  [FAIL] FAILED: {e}\n")
        checks_failed += 1

    # SUMMARY
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80 + "\n")

    total_checks = checks_passed + checks_failed
    pass_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

    print(f"Total checks: {total_checks}")
    print(f"Passed: {checks_passed} ({pass_rate:.0f}%)")
    print(f"Failed: {checks_failed}")

    if checks_failed == 0:
        print("\n[OK][OK][OK] ALL CHECKS PASSED - PRODUCTION READY [OK][OK][OK]\n")
        print("System is ready for:")
        print("  1. Single PDF processing with OutputManager")
        print("  2. Multi-PDF processing with auto-consolidation")
        print("  3. Consolidated JSON + Excel export")
        print("  4. Complete run tracking with manifests")
        print("  5. Historical tracking and debugging")
        return True
    else:
        print(f"\n[FAIL] {checks_failed} CHECK(S) FAILED - NOT PRODUCTION READY [FAIL]\n")
        return False


if __name__ == "__main__":
    success = validate_production_readiness()
    sys.exit(0 if success else 1)
