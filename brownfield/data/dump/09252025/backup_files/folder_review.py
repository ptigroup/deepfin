#!/usr/bin/env python3
"""
Optimized Folder Review Script

Provides a comprehensive overview of the output directory structure
showing file counts, sizes, and organization status.
"""

import os
from pathlib import Path
from datetime import datetime

def format_size(size_bytes):
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_directory_stats(path):
    """Get file count and total size for a directory."""
    total_files = 0
    total_size = 0
    
    try:
        for item in Path(path).rglob("*"):
            if item.is_file():
                total_files += 1
                total_size += item.stat().st_size
    except:
        pass
    
    return total_files, total_size

def review_folders():
    """Review the output folder structure."""
    base_dir = Path("output")
    
    print("📊 Enterprise Output Directory Review")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Main output directory
    main_files = [f for f in base_dir.iterdir() if f.is_file()]
    if main_files:
        main_file_count = len(main_files)
        main_size = sum(f.stat().st_size for f in main_files)
        print(f"🚨 MAIN OUTPUT FOLDER (should be clean):")
        print(f"   Files: {main_file_count} files ({format_size(main_size)})")
        print(f"   Status: {'❌ NEEDS CLEANUP' if main_file_count > 4 else '✅ CLEAN'}")
        
        if main_file_count <= 10:  # Show details if not too many
            for f in main_files:
                size = format_size(f.stat().st_size)
                print(f"   • {f.name} ({size})")
    else:
        print(f"✅ MAIN OUTPUT FOLDER: Clean (0 files)")
    
    print()
    
    # Subdirectories analysis
    subdirs = {
        "runs": "🏃 Run Directories (timestamped execution records)",
        "audit": "🔍 Audit Trail (complete intermediate files)",
        "orphaned": "🗂️ Orphaned Files (files without timestamps)"
    }
    
    for subdir, description in subdirs.items():
        subdir_path = base_dir / subdir
        if subdir_path.exists():
            file_count, total_size = get_directory_stats(subdir_path)
            
            print(f"{description}")
            print(f"   Location: output/{subdir}/")
            print(f"   Content: {file_count} files ({format_size(total_size)})")
            
            # Special handling for runs directory
            if subdir == "runs" and subdir_path.exists():
                run_dirs = [d for d in subdir_path.iterdir() if d.is_dir()]
                success_runs = [d for d in run_dirs if "SUCCESS" in d.name]
                processing_runs = [d for d in run_dirs if "PROCESSING" in d.name]
                failed_runs = [d for d in run_dirs if "FAILED" in d.name]
                
                print(f"   Runs: {len(run_dirs)} total")
                print(f"   • ✅ Successful: {len(success_runs)}")
                print(f"   • 🔄 Processing: {len(processing_runs)} {'(⚠️ STALE)' if processing_runs else ''}")
                print(f"   • ❌ Failed: {len(failed_runs)}")
                
                # Show latest runs
                if run_dirs:
                    latest_runs = sorted(run_dirs, key=lambda x: x.name, reverse=True)[:3]
                    print(f"   Latest:")
                    for run_dir in latest_runs:
                        run_files, run_size = get_directory_stats(run_dir)
                        print(f"   • {run_dir.name}: {run_files} files ({format_size(run_size)})")
            
            # Special handling for audit directory
            elif subdir == "audit" and subdir_path.exists():
                audit_runs = [d for d in subdir_path.iterdir() if d.is_dir()]
                print(f"   Audit Runs: {len(audit_runs)}")
                for audit_run in sorted(audit_runs, reverse=True)[:3]:
                    run_files, run_size = get_directory_stats(audit_run)
                    print(f"   • {audit_run.name}: {run_files} files ({format_size(run_size)})")
            
            
            print()
        else:
            print(f"{description}")
            print(f"   Status: Directory not found")
            print()
    
    # Summary and recommendations
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("-" * 40)
    
    total_main_files = len([f for f in base_dir.iterdir() if f.is_file()])
    
    if total_main_files == 0:
        print("✅ Output directory is properly organized")
        print("✅ All files are in appropriate subdirectories")
    elif total_main_files <= 4:
        print("⚠️ Output directory mostly clean (few system files)")
        print("✅ Organization is good")
    else:
        print("❌ Output directory needs cleanup")
        print("🔧 Recommendation: Run cleanup script to organize files")
        print("   Command: python3 cleanup_existing_files.py")
    
    # Mode recommendations
    runs_dir = base_dir / "runs"
    audit_dir = base_dir / "audit"
    
    if audit_dir.exists() and any(audit_dir.iterdir()):
        print("🔍 Audit mode detected - full intermediate file trail available")
    elif runs_dir.exists():
        print("🏭 Production mode detected - only final consolidated files retained")
    
    print("\n💡 MODE USAGE:")
    print("   MODE=production   → Clean output, only final files")
    print("   MODE=development  → Keep recent files for debugging")
    print("   MODE=audit        → Complete trail in audit/ directory")

if __name__ == "__main__":
    review_folders()