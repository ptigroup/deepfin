#!/usr/bin/env python3
"""
Merge Status Files

Creates a comprehensive STATUS.json by merging LATEST_STATUS.json and METADATA.json,
keeping the rich information from METADATA while maintaining simple access.
"""

import json
from pathlib import Path

def merge_status_files():
    """Merge the two status files into a comprehensive STATUS.json."""
    
    # Read existing files
    latest_status_path = Path("output/LATEST_STATUS.json")
    metadata_path = Path("output/METADATA.json")
    
    latest_status = {}
    metadata = {}
    
    if latest_status_path.exists():
        with open(latest_status_path, 'r') as f:
            latest_status = json.load(f)
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    # Create comprehensive status by merging both
    # Use metadata as base (comprehensive) and add any missing fields from latest_status
    merged_status = metadata.copy()
    
    # Ensure we have the simple access fields at the top level
    merged_status.update({
        "latest_run_id": metadata.get("run_id", latest_status.get("latest_run_id")),
        "status": metadata.get("status", latest_status.get("status")),
        "timestamp": latest_status.get("timestamp", metadata.get("end_time")),
        "mode": metadata.get("mode", latest_status.get("mode"))
    })
    
    # Final files paths should already be in correct structure
    
    # Write merged status
    status_path = Path("output/STATUS.json")
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(merged_status, f, indent=2)
    
    print(f"✅ Created comprehensive STATUS.json ({len(merged_status)} fields)")
    print(f"  • Run ID: {merged_status.get('latest_run_id')}")
    print(f"  • Status: {merged_status.get('status')}")
    print(f"  • Mode: {merged_status.get('mode')}")
    print(f"  • Duration: {merged_status.get('duration_seconds', 0):.1f}s")
    print(f"  • Files tracked: {len(merged_status.get('file_manifest', {}))}")

if __name__ == "__main__":
    merge_status_files()