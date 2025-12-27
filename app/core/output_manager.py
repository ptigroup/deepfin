"""
Output Manager for Hybrid Pipeline - Session 17.5

Manages run-based output structure with historical tracking, quick access,
and comprehensive metadata.

Structure:
    output/
    ├── runs/
    │   ├── latest -> 20251227_134500_SUCCESS/
    │   └── 20251227_134500_SUCCESS/
    │       ├── run_manifest.json
    │       ├── run.log
    │       ├── extracted/
    │       │   └── {pdf_name}/
    │       │       ├── {statement_type}.json
    │       │       ├── {statement_type}.xlsx
    │       │       ├── raw_text.txt
    │       │       ├── metadata.json
    │       │       └── validation.json
    │       └── consolidated/
    │           ├── {statement_type}_{years}.json
    │           └── {statement_type}_{years}.xlsx
    ├── by_document/
    │   └── {pdf_name}/
    │       ├── latest -> ../../runs/latest/extracted/{pdf_name}/
    │       └── history.json
    └── by_statement/
        └── {statement_type}/
            └── latest_consolidated.json -> symlink
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RunStatus:
    """Run status constants."""
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ExtractionRun:
    """Represents a single extraction run with all its outputs."""

    def __init__(self, run_id: str, output_base: Path, status: str = RunStatus.IN_PROGRESS):
        self.run_id = run_id
        self.output_base = Path(output_base)
        self.status = status

        # Create run folder
        self.run_dir = self.output_base / "runs" / f"{run_id}_{status}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.extracted_dir = self.run_dir / "extracted"
        self.consolidated_dir = self.run_dir / "consolidated"
        self.extracted_dir.mkdir(exist_ok=True)
        self.consolidated_dir.mkdir(exist_ok=True)

        # Initialize manifest
        self.manifest = {
            "run_id": run_id,
            "status": status,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "duration_seconds": 0,
            "total_cost_usd": 0.0,
            "settings": {},
            "pdfs_processed": [],
            "consolidated": [],
            "summary": {
                "total_pdfs": 0,
                "successful": 0,
                "failed": 0,
                "total_statements": 0,
                "total_line_items": 0,
                "total_cost_usd": 0.0,
                "cost_savings_percent": 0.0
            }
        }

        self._save_manifest()
        logger.info(f"Created extraction run: {self.run_id} ({status})")

    def save_extraction(
        self,
        pdf_name: str,
        statement_type: str,
        json_data: Dict,
        excel_path: Optional[str] = None,
        raw_text: Optional[str] = None,
        metadata: Optional[Dict] = None,
        validation: Optional[Dict] = None,
        page_detection: Optional[Dict] = None
    ) -> Path:
        """Save extraction outputs for a single PDF."""

        # Create PDF-specific directory
        pdf_dir = self.extracted_dir / pdf_name
        pdf_dir.mkdir(exist_ok=True)

        # Save JSON
        json_path = pdf_dir / f"{statement_type}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)

        # Save Excel if provided
        if excel_path and os.path.exists(excel_path):
            excel_dest = pdf_dir / f"{statement_type}.xlsx"
            shutil.copy2(excel_path, excel_dest)

        # Save raw text if provided
        if raw_text:
            raw_path = pdf_dir / "raw_text.txt"
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(raw_text)

        # Save metadata if provided
        if metadata:
            meta_path = pdf_dir / "metadata.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

        # Save validation if provided
        if validation:
            val_path = pdf_dir / "validation.json"
            with open(val_path, 'w', encoding='utf-8') as f:
                json.dump(validation, f, indent=2)

        # Save page detection if provided
        if page_detection:
            pd_path = pdf_dir / "page_detection.json"
            with open(pd_path, 'w', encoding='utf-8') as f:
                json.dump(page_detection, f, indent=2)

        logger.info(f"Saved extraction for {pdf_name} -> {pdf_dir}")
        return pdf_dir

    def add_pdf_result(
        self,
        filename: str,
        pages_total: int,
        pages_extracted: List[int],
        status: str,
        statements_found: List[str],
        extraction_method: str = "",
        accuracy: float = 0.0,
        cost_usd: float = 0.0,
        duration_seconds: float = 0.0,
        line_items: int = 0,
        error: Optional[str] = None
    ):
        """Add PDF processing result to manifest."""

        result = {
            "filename": filename,
            "pages_total": pages_total,
            "pages_extracted": pages_extracted,
            "status": status,
            "statements_found": statements_found,
            "extraction_method": extraction_method,
            "accuracy": accuracy,
            "cost_usd": cost_usd,
            "duration_seconds": duration_seconds,
            "line_items": line_items
        }

        if error:
            result["error"] = error

        self.manifest["pdfs_processed"].append(result)

        # Update summary
        self.manifest["summary"]["total_pdfs"] += 1
        if status == "SUCCESS":
            self.manifest["summary"]["successful"] += 1
        else:
            self.manifest["summary"]["failed"] += 1

        self.manifest["summary"]["total_cost_usd"] += cost_usd
        self.manifest["summary"]["total_line_items"] += line_items

        self._save_manifest()

    def save_consolidated(
        self,
        statement_type: str,
        years: List[str],
        json_data: Dict,
        excel_path: Optional[str] = None,
        source_count: int = 0,
        line_items: int = 0
    ) -> Path:
        """Save consolidated multi-PDF output."""

        # Determine year range for filename
        if len(years) > 1:
            year_range = f"{years[0]}-{years[-1]}"
        else:
            year_range = years[0] if years else "unknown"

        # Save JSON
        json_path = self.consolidated_dir / f"{statement_type}_{year_range}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)

        # Save Excel if provided
        if excel_path and os.path.exists(excel_path):
            excel_dest = self.consolidated_dir / f"{statement_type}_{year_range}.xlsx"
            shutil.copy2(excel_path, excel_dest)

        # Add to manifest
        self.manifest["consolidated"].append({
            "statement_type": statement_type,
            "years": years,
            "source_count": source_count,
            "line_items": line_items,
            "output_files": [
                f"consolidated/{statement_type}_{year_range}.json",
                f"consolidated/{statement_type}_{year_range}.xlsx" if excel_path else None
            ]
        })

        self.manifest["summary"]["total_statements"] += 1
        self._save_manifest()

        logger.info(f"Saved consolidated {statement_type} ({year_range}) -> {json_path}")
        return self.consolidated_dir

    def set_settings(self, settings: Dict):
        """Set processing settings in manifest."""
        self.manifest["settings"] = settings
        self._save_manifest()

    def complete(self, status: str = RunStatus.SUCCESS):
        """Mark run as complete and update status."""

        # Calculate duration
        started = datetime.fromisoformat(self.manifest["started_at"])
        completed = datetime.now()
        duration = (completed - started).total_seconds()

        self.manifest["status"] = status
        self.manifest["completed_at"] = completed.isoformat()
        self.manifest["duration_seconds"] = duration

        self._save_manifest()

        # Rename folder to include final status if changed
        if status != self.status:
            new_run_dir = self.output_base / "runs" / f"{self.run_id}_{status}"
            if self.run_dir != new_run_dir:
                self.run_dir.rename(new_run_dir)
                self.run_dir = new_run_dir
                logger.info(f"Renamed run folder to {new_run_dir.name}")

        # Update 'latest' symlink if successful
        if status == RunStatus.SUCCESS:
            self._update_latest_symlink()

        logger.info(f"Completed run {self.run_id} with status {status}")

    def _save_manifest(self):
        """Save run manifest to file."""
        manifest_path = self.run_dir / "run_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)

    def _update_latest_symlink(self):
        """Update 'latest' symlink to point to this run."""
        runs_dir = self.output_base / "runs"
        latest_link = runs_dir / "latest"

        # Remove existing symlink if it exists
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()

        # Create new symlink
        try:
            # Use relative path for portability
            latest_link.symlink_to(self.run_dir.name, target_is_directory=True)
            logger.info(f"Updated 'latest' symlink -> {self.run_dir.name}")
        except OSError as e:
            # Symlinks might not work on Windows without admin rights
            logger.warning(f"Could not create symlink: {e}")
            # Fallback: create a text file with the path
            with open(runs_dir / "latest.txt", 'w') as f:
                f.write(self.run_dir.name)
            logger.info(f"Created latest.txt -> {self.run_dir.name}")


class OutputManager:
    """Manages output structure for hybrid pipeline extractions."""

    def __init__(self, output_base: str = "output"):
        """Initialize output manager.

        Args:
            output_base: Base directory for all outputs (default: "output")
        """
        self.output_base = Path(output_base)
        self._ensure_structure()
        logger.info(f"OutputManager initialized: {self.output_base}")

    def _ensure_structure(self):
        """Ensure output directory structure exists."""
        # Create base directories
        (self.output_base / "runs").mkdir(parents=True, exist_ok=True)
        (self.output_base / "by_document").mkdir(parents=True, exist_ok=True)
        (self.output_base / "by_statement").mkdir(parents=True, exist_ok=True)
        (self.output_base / "cache" / "llmwhisperer").mkdir(parents=True, exist_ok=True)
        (self.output_base / "cache" / "page_detection").mkdir(parents=True, exist_ok=True)

    def create_run(self, status: str = RunStatus.IN_PROGRESS) -> ExtractionRun:
        """Create a new extraction run.

        Args:
            status: Initial run status (default: IN_PROGRESS)

        Returns:
            ExtractionRun instance
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return ExtractionRun(run_id, self.output_base, status)

    def get_latest_run(self) -> Optional[Path]:
        """Get path to latest successful run.

        Returns:
            Path to latest run directory or None
        """
        runs_dir = self.output_base / "runs"
        latest_link = runs_dir / "latest"

        if latest_link.is_symlink() or latest_link.is_dir():
            return latest_link

        # Fallback: check latest.txt
        latest_txt = runs_dir / "latest.txt"
        if latest_txt.exists():
            with open(latest_txt) as f:
                run_name = f.read().strip()
                return runs_dir / run_name

        return None

    def get_run_by_id(self, run_id: str) -> Optional[Path]:
        """Get path to specific run by ID.

        Args:
            run_id: Run ID (timestamp format: YYYYMMDD_HHMMSS)

        Returns:
            Path to run directory or None
        """
        runs_dir = self.output_base / "runs"

        # Find folder starting with run_id
        for folder in runs_dir.iterdir():
            if folder.is_dir() and folder.name.startswith(run_id):
                return folder

        return None

    def list_runs(self, status: Optional[str] = None) -> List[Dict]:
        """List all runs with their metadata.

        Args:
            status: Filter by status (SUCCESS, PARTIAL, FAILED)

        Returns:
            List of run manifests
        """
        runs_dir = self.output_base / "runs"
        runs = []

        for folder in sorted(runs_dir.iterdir(), reverse=True):
            if folder.is_dir() and not folder.name.startswith("latest"):
                manifest_path = folder / "run_manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)

                    # Filter by status if specified
                    if status is None or manifest.get("status") == status:
                        runs.append(manifest)

        return runs

    def get_latest_by_document(self, pdf_name: str) -> Optional[Path]:
        """Get latest extraction for a specific document.

        Args:
            pdf_name: PDF name (without extension)

        Returns:
            Path to document directory in latest run or None
        """
        latest_run = self.get_latest_run()
        if latest_run:
            doc_dir = latest_run / "extracted" / pdf_name
            if doc_dir.exists():
                return doc_dir

        return None

    def get_cache_path(self, cache_type: str, key: str) -> Path:
        """Get path for cached data.

        Args:
            cache_type: Type of cache (llmwhisperer, page_detection)
            key: Cache key (usually filename or hash)

        Returns:
            Path to cache file
        """
        return self.output_base / "cache" / cache_type / key

    def cleanup_old_runs(self, keep_count: int = 10):
        """Remove old runs, keeping only the most recent.

        Args:
            keep_count: Number of runs to keep (default: 10)
        """
        runs_dir = self.output_base / "runs"

        # Get all run folders sorted by name (timestamp)
        run_folders = sorted(
            [f for f in runs_dir.iterdir() if f.is_dir() and not f.name.startswith("latest")],
            reverse=True
        )

        # Remove old runs beyond keep_count
        for folder in run_folders[keep_count:]:
            logger.info(f"Removing old run: {folder.name}")
            shutil.rmtree(folder)
