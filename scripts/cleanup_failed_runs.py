"""
Clean up failed or incomplete processing runs.

This script removes:
1. IN_PROGRESS runs older than 1 hour (likely crashed)
2. Empty or minimal runs (< 50KB)
3. Optionally: runs before a specific date
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.path_config import PathConfig


def cleanup_failed_runs(
    output_dir: Path,
    max_age_hours: int = 1,
    min_size_kb: int = 50,
    dry_run: bool = True
):
    """
    Clean up failed runs from output directory.

    Args:
        output_dir: Path to output/runs directory
        max_age_hours: Remove IN_PROGRESS runs older than this
        min_size_kb: Remove runs smaller than this (likely incomplete)
        dry_run: If True, only show what would be deleted
    """
    if not output_dir.exists():
        print(f"Output directory not found: {output_dir}")
        return

    now = datetime.now()
    cutoff_time = now - timedelta(hours=max_age_hours)

    deleted_count = 0
    total_size_freed = 0

    print(f"Scanning: {output_dir}")
    print(f"Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Minimum size: {min_size_kb}KB")
    print(f"Mode: {'DRY RUN' if dry_run else 'DELETE'}\n")

    # Find all run directories
    run_dirs = sorted(output_dir.glob("20*"))

    for run_dir in run_dirs:
        if not run_dir.is_dir():
            continue

        # Get run info
        run_name = run_dir.name
        created_time = datetime.fromtimestamp(run_dir.stat().st_ctime)
        age_hours = (now - created_time).total_seconds() / 3600

        # Calculate directory size
        total_size = sum(f.stat().st_size for f in run_dir.rglob('*') if f.is_file())
        size_kb = total_size / 1024

        # Determine if should delete
        should_delete = False
        reason = ""

        if "_IN_PROGRESS" in run_name:
            if age_hours > max_age_hours:
                should_delete = True
                reason = f"IN_PROGRESS run older than {max_age_hours}h ({age_hours:.1f}h)"

        if size_kb < min_size_kb:
            should_delete = True
            reason = f"Run too small ({size_kb:.1f}KB < {min_size_kb}KB)"

        if should_delete:
            print(f"{'[DELETE]' if not dry_run else '[WOULD DELETE]'}: {run_name}")
            print(f"  Reason: {reason}")
            print(f"  Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Size: {size_kb:.1f}KB")

            if not dry_run:
                shutil.rmtree(run_dir)
                print(f"  [OK] Deleted")

            deleted_count += 1
            total_size_freed += size_kb
            print()

    print(f"\n{'Would delete' if dry_run else 'Deleted'}: {deleted_count} run(s)")
    print(f"{'Would free' if dry_run else 'Freed'}: {total_size_freed:.1f}KB ({total_size_freed/1024:.1f}MB)")

    if dry_run and deleted_count > 0:
        print("\nRe-run with --execute to actually delete these runs")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up failed or incomplete processing runs"
    )
    parser.add_argument(
        "--mode",
        choices=["production", "testing"],
        default="production",
        help="Which output directory to clean (default: production)"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=1,
        help="Remove IN_PROGRESS runs older than this many hours (default: 1)"
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=50,
        help="Remove runs smaller than this many KB (default: 50)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (default: dry run)"
    )

    args = parser.parse_args()

    # Get output directory based on mode
    config = PathConfig(mode=args.mode)
    output_dir = config.output_runs_dir

    # Run cleanup
    cleanup_failed_runs(
        output_dir=output_dir,
        max_age_hours=args.max_age,
        min_size_kb=args.min_size,
        dry_run=not args.execute
    )


if __name__ == "__main__":
    main()
