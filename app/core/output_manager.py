"""
Output Manager for Hybrid Pipeline - Enhanced

Manages run-based output structure with historical tracking, quick access,
cost tracking, checksums, and comprehensive metadata.

Structure:
    output/
    ├── runs/
    │   ├── latest -> 20251228_101019_SUCCESS/
    │   └── 20251228_101019_SUCCESS/
    │       ├── run_manifest.json      # Complete metadata + costs
    │       ├── checksums.md5           # File integrity
    │       ├── extracted/
    │       │   └── {pdf_name}/
    │       │       ├── {statement_type}.json
    │       │       ├── {statement_type}.xlsx
    │       │       ├── raw_text.txt          # LLMWhisperer output
    │       │       ├── metadata.json         # Pages, timing
    │       │       └── validation.json
    │       └── consolidated/
    │           ├── {statement_type}_{years}.json
    │           ├── {statement_type}_{years}.xlsx
    │           └── all_statements_{years}.xlsx  # Combined
    ├── LATEST_OUTPUTS/                 # Quick access
    │   ├── all_statements.xlsx
    │   └── run_manifest.json
    └── RUN_HISTORY.md                  # Human-readable summary
"""

import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

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
                "cost_savings_percent": 0.0,
            },
        }

        self._save_manifest()
        logger.info(f"Created extraction run: {self.run_id} ({status})")

    def save_extraction(
        self,
        pdf_name: str,
        statement_type: str,
        json_data: dict,
        excel_path: str | None = None,
        raw_text: str | None = None,
        metadata: dict | None = None,
        validation: dict | None = None,
        page_detection: dict | None = None,
    ) -> Path:
        """Save extraction outputs for a single PDF."""

        # Create PDF-specific directory
        pdf_dir = self.extracted_dir / pdf_name
        pdf_dir.mkdir(exist_ok=True)

        # Save JSON
        json_path = pdf_dir / f"{statement_type}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        # Save Excel if provided
        if excel_path and os.path.exists(excel_path):
            excel_dest = pdf_dir / f"{statement_type}.xlsx"
            shutil.copy2(excel_path, excel_dest)

        # Save raw text if provided
        if raw_text:
            raw_path = pdf_dir / "raw_text.txt"
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(raw_text)

        # Save metadata if provided
        if metadata:
            meta_path = pdf_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        # Save validation if provided
        if validation:
            val_path = pdf_dir / "validation.json"
            with open(val_path, "w", encoding="utf-8") as f:
                json.dump(validation, f, indent=2)

        # Save page detection if provided
        if page_detection:
            pd_path = pdf_dir / "page_detection.json"
            with open(pd_path, "w", encoding="utf-8") as f:
                json.dump(page_detection, f, indent=2)

        logger.info(f"Saved extraction for {pdf_name} -> {pdf_dir}")
        return pdf_dir

    def add_pdf_result(
        self,
        filename: str,
        pages_total: int,
        pages_extracted: list[int],
        status: str,
        statements_found: list[str],
        extraction_method: str = "",
        accuracy: float = 0.0,
        cost_usd: float = 0.0,
        duration_seconds: float = 0.0,
        line_items: int = 0,
        error: str | None = None,
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
            "line_items": line_items,
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
        years: list[str],
        json_data: dict,
        excel_path: str | None = None,
        source_count: int = 0,
        line_items: int = 0,
    ) -> Path:
        """Save consolidated multi-PDF output."""

        # Determine year range for filename
        if len(years) > 1:
            year_range = f"{years[0]}-{years[-1]}"
        else:
            year_range = years[0] if years else "unknown"

        # Save JSON
        json_path = self.consolidated_dir / f"{statement_type}_{year_range}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        # Save Excel if provided
        if excel_path and os.path.exists(excel_path):
            excel_dest = self.consolidated_dir / f"{statement_type}_{year_range}.xlsx"
            shutil.copy2(excel_path, excel_dest)

        # Add to manifest
        self.manifest["consolidated"].append(
            {
                "statement_type": statement_type,
                "years": years,
                "source_count": source_count,
                "line_items": line_items,
                "output_files": [
                    f"consolidated/{statement_type}_{year_range}.json",
                    f"consolidated/{statement_type}_{year_range}.xlsx" if excel_path else None,
                ],
            }
        )

        self.manifest["summary"]["total_statements"] += 1
        self._save_manifest()

        logger.info(f"Saved consolidated {statement_type} ({year_range}) -> {json_path}")
        return self.consolidated_dir

    def set_settings(self, settings: dict):
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

        # Generate checksums for all output files
        self._generate_checksums()

        # Rename folder to include final status if changed
        if status != self.status:
            new_run_dir = self.output_base / "runs" / f"{self.run_id}_{status}"
            if self.run_dir != new_run_dir:
                self.run_dir.rename(new_run_dir)
                self.run_dir = new_run_dir
                logger.info(f"Renamed run folder to {new_run_dir.name}")

        # Always update run history
        self._update_run_history()

        # Update 'latest' symlink and outputs if successful
        if status == RunStatus.SUCCESS:
            self._update_latest_symlink()
            self._update_latest_outputs()

        logger.info(f"Completed run {self.run_id} with status {status}")

    def _save_manifest(self):
        """Save run manifest to file."""
        manifest_path = self.run_dir / "run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
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
            with open(runs_dir / "latest.txt", "w") as f:
                f.write(self.run_dir.name)
            logger.info(f"Created latest.txt -> {self.run_dir.name}")

    def _generate_checksums(self):
        """Generate MD5 checksums for all output files."""
        checksums = []

        # Calculate checksums for all files in run directory
        for file_path in sorted(self.run_dir.rglob("*")):
            if file_path.is_file() and file_path.name not in ["checksums.md5", "run_manifest.json"]:
                md5_hash = hashlib.md5()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)

                # Use relative path from run directory
                rel_path = file_path.relative_to(self.run_dir)
                checksums.append(f"{md5_hash.hexdigest()}  {rel_path}")

        # Write checksums file
        checksum_file = self.run_dir / "checksums.md5"
        with open(checksum_file, "w") as f:
            f.write("# MD5 Checksums for Run Output Files\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Run ID: {self.run_id}\n\n")
            f.write("\n".join(checksums))

        logger.info(f"Generated checksums for {len(checksums)} files")

    def _update_latest_outputs(self):
        """Copy latest successful outputs to LATEST_OUTPUTS for quick access."""
        latest_outputs_dir = self.output_base / "LATEST_OUTPUTS"
        latest_outputs_dir.mkdir(exist_ok=True)

        # Clear existing files
        for file_path in latest_outputs_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()

        # Copy combined outputs from consolidated directory
        combined_files = list(self.consolidated_dir.glob("all_statements_*.xlsx"))
        combined_files.extend(self.consolidated_dir.glob("all_statements_*.json"))

        for src in combined_files:
            dest = latest_outputs_dir / src.name
            shutil.copy2(src, dest)

        # Copy manifest
        manifest_src = self.run_dir / "run_manifest.json"
        if manifest_src.exists():
            shutil.copy2(manifest_src, latest_outputs_dir / "run_manifest.json")

        logger.info(f"Updated LATEST_OUTPUTS with {len(combined_files)} files")

    def _update_run_history(self):
        """Update RUN_HISTORY.md with this run's summary."""
        history_file = self.output_base / "RUN_HISTORY.md"

        # Read existing history
        existing_entries = []
        if history_file.exists():
            with open(history_file, encoding="utf-8") as f:
                content = f.read()
                # Keep header
                if content.startswith("# Run History"):
                    parts = content.split("\n---\n", 1)
                    if len(parts) > 1:
                        entries = parts[1].strip().split("\n---\n")
                        existing_entries = [e for e in entries if e.strip()]

        # Create new entry
        summary = self.manifest.get("summary", {})
        new_entry = f"""
## Run: {self.run_id} ({self.manifest["status"]})

**Timestamp**: {self.manifest["completed_at"] or self.manifest["started_at"]}
**Duration**: {self.manifest.get("duration_seconds", 0):.1f} seconds
**Status**: {self.manifest["status"]}

### Summary
- **PDFs Processed**: {summary.get("total_pdfs", 0)}
- **Successful**: {summary.get("successful", 0)}
- **Failed**: {summary.get("failed", 0)}
- **Total Statements**: {summary.get("total_statements", 0)}
- **Total Line Items**: {summary.get("total_line_items", 0)}
- **Total Cost**: ${summary.get("total_cost_usd", 0.0):.2f}

### PDFs
{self._format_pdf_list()}

### Consolidated Outputs
{self._format_consolidated_list()}

**Run Directory**: `{self.run_dir.relative_to(self.output_base)}`
""".strip()

        # Write history file
        with open(history_file, "w", encoding="utf-8") as f:
            f.write("# Run History\n\n")
            f.write("**Latest runs shown first**\n\n")
            f.write("---\n\n")
            f.write(new_entry)

            # Add previous entries (limit to 20 most recent)
            for entry in existing_entries[:20]:
                f.write("\n\n---\n\n")
                f.write(entry.strip())

        logger.info("Updated RUN_HISTORY.md")

    def _format_pdf_list(self) -> str:
        """Format PDF list for history entry."""
        lines = []
        for pdf in self.manifest.get("pdfs_processed", []):
            status_icon = "✅" if pdf["status"] == "SUCCESS" else "❌"
            lines.append(
                f"- {status_icon} **{pdf['filename']}**: "
                f"{len(pdf.get('statements_found', []))} statements, "
                f"{pdf.get('line_items', 0)} line items, "
                f"${pdf.get('cost_usd', 0):.2f}"
            )
        return "\n".join(lines) if lines else "- (No PDFs processed)"

    def _format_consolidated_list(self) -> str:
        """Format consolidated outputs for history entry."""
        lines = []
        for item in self.manifest.get("consolidated", []):
            years = item.get("years", [])
            year_range = (
                f"{years[0]}-{years[-1]}" if len(years) > 1 else years[0] if years else "unknown"
            )
            lines.append(
                f"- **{item['statement_type']}** ({year_range}): "
                f"{item.get('source_count', 0)} sources, {item.get('line_items', 0)} line items"
            )
        return "\n".join(lines) if lines else "- (No consolidated outputs)"


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

        # Cache directories for future performance optimization
        # TODO: Implement caching to reduce API calls
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

    def get_latest_run(self) -> Path | None:
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

    def get_run_by_id(self, run_id: str) -> Path | None:
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

    def list_runs(self, status: str | None = None) -> list[dict]:
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

    def get_latest_by_document(self, pdf_name: str) -> Path | None:
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
            reverse=True,
        )

        # Remove old runs beyond keep_count
        for folder in run_folders[keep_count:]:
            logger.info(f"Removing old run: {folder.name}")
            shutil.rmtree(folder)
