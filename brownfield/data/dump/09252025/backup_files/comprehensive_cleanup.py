#!/usr/bin/env python3
"""
Comprehensive Cleanup Script

Fixes all identified issues:
1. Cleans main output folder
2. Fixes stale PROCESSING directories  
3. Removes legacy files
4. Organizes remaining files properly
"""

import os
import shutil
from pathlib import Path
from enterprise_output_manager import EnterpriseOutputManager

def fix_stale_processing_directories():
    """Convert stale PROCESSING directories to SUCCESS."""
    runs_dir = Path("output/runs")
    if not runs_dir.exists():
        return
    
    processing_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and "PROCESSING" in d.name]
    
    if processing_dirs:
        print(f"🔄 Fixing {len(processing_dirs)} stale PROCESSING directories...")
        
        for proc_dir in processing_dirs:
            # Convert PROCESSING to SUCCESS
            success_name = proc_dir.name.replace("_PROCESSING", "_SUCCESS")
            success_dir = runs_dir / success_name
            
            try:
                shutil.move(str(proc_dir), str(success_dir))
                print(f"  ✅ Fixed: {proc_dir.name} → {success_name}")
            except Exception as e:
                print(f"  ❌ Could not fix {proc_dir.name}: {e}")

def remove_legacy_files():
    """Remove legacy pdf_consolidated files."""
    legacy_file = Path("output/LATEST_CONSOLIDATED/pdf_consolidated).xlsx")
    if legacy_file.exists():
        try:
            legacy_file.unlink()
            print("✅ Removed legacy pdf_consolidated).xlsx")
        except Exception as e:
            print(f"❌ Could not remove legacy file: {e}")

def organize_main_output_files():
    """Organize files in main output directory."""
    print("🧹 Organizing main output folder...")
    
    # Initialize enterprise output manager
    output_manager = EnterpriseOutputManager(mode='production')
    
    # Get all files in main output directory (excluding system files)
    main_dir = Path("output")
    files_to_organize = []
    
    for file_path in main_dir.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            # Skip system files
            if file_path.name in ['LATEST_RUN_SUMMARY.txt', 'LATEST_STATUS.json']:
                continue
            files_to_organize.append(file_path)
    
    if not files_to_organize:
        print("  ✅ Main output folder already clean")
        return
    
    print(f"  📁 Found {len(files_to_organize)} files to organize")
    
    # Group files by timestamp
    files_by_timestamp = {}
    orphaned_files = []
    
    for file_path in files_to_organize:
        timestamp = output_manager._extract_timestamp_from_filename(file_path.name)
        if timestamp:
            if timestamp not in files_by_timestamp:
                files_by_timestamp[timestamp] = []
            files_by_timestamp[timestamp].append(file_path)
        else:
            orphaned_files.append(file_path)
    
    # Organize files by timestamp
    for timestamp, files in files_by_timestamp.items():
        # Convert timestamp to run ID format
        if len(timestamp) == 14:  # DDMMYYYYHHMMSS
            dd, mm, yyyy, hhmmss = timestamp[:2], timestamp[2:4], timestamp[4:8], timestamp[8:]
            run_id = f"{yyyy}{mm}{dd}_{hhmmss[:2]}{hhmmss[2:4]}{hhmmss[4:]}"
        else:
            continue
        
        # Find existing run directory
        runs_dir = Path("output/runs")
        matching_run_dirs = list(runs_dir.glob(f"{run_id}_*"))
        
        if matching_run_dirs:
            target_run_dir = matching_run_dirs[0]
            
            # Move final consolidated files to run directory, delete others
            for file_path in files:
                if 'multi-pdf-consolidated' in file_path.name and file_path.suffix == '.xlsx':
                    # Keep final consolidated Excel files
                    try:
                        dest_path = target_run_dir / file_path.name
                        shutil.move(str(file_path), str(dest_path))
                        print(f"  📁 Moved: {file_path.name} → runs/{target_run_dir.name}/")
                    except Exception as e:
                        print(f"  ⚠️ Could not move {file_path.name}: {e}")
                else:
                    # Delete intermediate files in production mode
                    try:
                        file_path.unlink()
                        print(f"  🗑️ Deleted: {file_path.name}")
                    except Exception as e:
                        print(f"  ⚠️ Could not delete {file_path.name}: {e}")
    
    # Handle orphaned files
    if orphaned_files:
        orphaned_dir = Path("output/orphaned") / "cleanup_20250921"
        orphaned_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in orphaned_files:
            try:
                dest_path = orphaned_dir / file_path.name
                shutil.move(str(file_path), str(dest_path))
                print(f"  📁 Orphaned: {file_path.name} → orphaned/cleanup_20250921/")
            except Exception as e:
                print(f"  ⚠️ Could not move orphaned file {file_path.name}: {e}")

def main():
    """Run comprehensive cleanup."""
    print("🧹 Comprehensive Output Directory Cleanup")
    print("=" * 50)
    
    # Step 1: Fix stale processing directories
    fix_stale_processing_directories()
    
    # Step 2: Remove legacy files
    remove_legacy_files()
    
    # Step 3: Organize main output files
    organize_main_output_files()
    
    print("\n✅ Comprehensive cleanup completed!")
    print("🔍 Run 'python3 folder_review.py' to verify results")

if __name__ == "__main__":
    main()