#!/usr/bin/env python3
"""
Cleanup Script for Existing Output Files

This script uses the EnterpriseOutputManager to clean up all existing files
in the main output directory and organize them properly according to the
enterprise file management system.
"""

import os
from enterprise_output_manager import EnterpriseOutputManager

def main():
    """Clean up existing files in output directory."""
    print("🧹 Starting Existing File Cleanup")
    print("=" * 50)
    
    # Initialize enterprise output manager
    mode = os.getenv('MODE', 'production').lower()
    output_manager = EnterpriseOutputManager(mode=mode)
    
    # Clean up existing files
    output_manager.cleanup_existing_files()
    
    print("\n✅ Cleanup completed!")
    print("=" * 50)
    print(f"Mode: {mode}")
    print("Check the following directories:")
    print("  • output/runs/ - Run directories with final files")
    if mode == 'audit':
        print("  • output/audit/ - Audit trails by timestamp")
    print("  • output/orphaned/ - Files without timestamps (if any)")
    print("  • output/ - Should now be clean!")

if __name__ == "__main__":
    main()