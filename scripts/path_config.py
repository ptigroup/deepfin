"""
Path Configuration for Financial Document Processing Pipeline

This module provides centralized path configuration for all processing scripts.
Supports both production and testing/sample environments.

Environment Variables:
    PROCESSING_MODE: "production" or "testing" (default: "testing")
    INPUT_DIR: Override default input directory
    OUTPUT_DIR: Override default output directory
    UPLOAD_DIR: Override default upload directory

Usage:
    from scripts.path_config import PathConfig

    config = PathConfig()
    print(config.input_dir)       # Path to input directory
    print(config.output_runs_dir) # Path to output/runs directory
"""

import os
from pathlib import Path
from typing import Literal

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class PathConfig:
    """Central configuration for file paths in the processing pipeline."""

    def __init__(
        self,
        mode: Literal["production", "testing"] | None = None,
        input_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        upload_dir: Path | str | None = None,
    ):
        """
        Initialize path configuration.

        Args:
            mode: Processing mode ("production" or "testing").
                  Defaults to environment variable PROCESSING_MODE or "testing".
            input_dir: Override input directory path.
            output_dir: Override output directory path.
            upload_dir: Override upload directory path.
        """
        # Determine mode from parameter, environment, or default
        self.mode = mode or os.getenv("PROCESSING_MODE", "testing")

        # Set base directories based on mode
        if self.mode == "production":
            self._set_production_paths()
        else:
            self._set_testing_paths()

        # Allow environment variable or parameter overrides
        if input_dir:
            self.input_dir = Path(input_dir)
        elif os.getenv("INPUT_DIR"):
            self.input_dir = Path(os.getenv("INPUT_DIR"))

        if output_dir:
            self.output_runs_dir = Path(output_dir)
        elif os.getenv("OUTPUT_DIR"):
            self.output_runs_dir = Path(os.getenv("OUTPUT_DIR"))

        if upload_dir:
            self.upload_dir = Path(upload_dir)
        elif os.getenv("UPLOAD_DIR"):
            self.upload_dir = Path(os.getenv("UPLOAD_DIR"))

    def _set_production_paths(self) -> None:
        """Set paths for production mode."""
        self.input_dir = PROJECT_ROOT / "input"
        self.upload_dir = PROJECT_ROOT / "uploads"
        self.output_runs_dir = PROJECT_ROOT / "output" / "runs"
        self.output_archive_dir = PROJECT_ROOT / "output" / "archive"

    def _set_testing_paths(self) -> None:
        """Set paths for testing/sample mode."""
        self.input_dir = PROJECT_ROOT / "samples" / "input"
        self.upload_dir = PROJECT_ROOT / "uploads"  # Still use main uploads
        self.output_runs_dir = PROJECT_ROOT / "samples" / "output" / "runs"
        self.output_archive_dir = PROJECT_ROOT / "samples" / "output" / "archive"

    def ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_runs_dir.mkdir(parents=True, exist_ok=True)
        self.output_archive_dir.mkdir(parents=True, exist_ok=True)

    def get_latest_run_id(self) -> str | None:
        """
        Get the ID of the most recent processing run.

        Returns:
            Run ID (timestamp) or None if no runs exist.
        """
        latest_file = self.output_runs_dir / "latest.txt"
        if latest_file.exists():
            return latest_file.read_text().strip()

        # Fallback: Find most recent run directory
        runs = sorted(self.output_runs_dir.glob("20*"))
        if runs:
            return runs[-1].name.split("_")[0] + "_" + runs[-1].name.split("_")[1]

        return None

    def get_run_dir(self, run_id: str, status: str = "IN_PROGRESS") -> Path:
        """
        Get the directory path for a specific run.

        Args:
            run_id: Run timestamp (e.g., "20251228_150533")
            status: Run status (SUCCESS, PARTIAL, FAILED, IN_PROGRESS)

        Returns:
            Path to run directory.
        """
        return self.output_runs_dir / f"{run_id}_{status}"

    def __repr__(self) -> str:
        return (
            f"PathConfig(mode='{self.mode}', "
            f"input='{self.input_dir}', "
            f"output='{self.output_runs_dir}')"
        )


# Default configuration singleton
default_config = PathConfig()


def get_config(mode: Literal["production", "testing"] | None = None) -> PathConfig:
    """
    Get path configuration instance.

    Args:
        mode: Processing mode. If None, uses default from environment.

    Returns:
        PathConfig instance.

    Examples:
        >>> # Use default (testing mode)
        >>> config = get_config()
        >>> config.input_dir
        PosixPath('/path/to/samples/input')

        >>> # Use production mode
        >>> config = get_config(mode="production")
        >>> config.input_dir
        PosixPath('/path/to/input')

        >>> # Override with environment variable
        >>> os.environ['PROCESSING_MODE'] = 'production'
        >>> config = get_config()
        >>> config.input_dir
        PosixPath('/path/to/input')
    """
    if mode:
        return PathConfig(mode=mode)
    return default_config


if __name__ == "__main__":
    # Demo usage
    print("=== Testing Mode (Default) ===")
    config_test = PathConfig(mode="testing")
    print(config_test)
    print(f"Input:  {config_test.input_dir}")
    print(f"Output: {config_test.output_runs_dir}")
    print(f"Upload: {config_test.upload_dir}")

    print("\n=== Production Mode ===")
    config_prod = PathConfig(mode="production")
    print(config_prod)
    print(f"Input:  {config_prod.input_dir}")
    print(f"Output: {config_prod.output_runs_dir}")
    print(f"Upload: {config_prod.upload_dir}")

    print("\n=== Ensure Directories ===")
    config_prod.ensure_directories()
    print("[OK] All directories created")
