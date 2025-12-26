#!/usr/bin/env python3
"""
Migration Safety Management System
Provides comprehensive safety measures for file structure refactoring including
cache management, metadata backup, and rollback capabilities.
"""

import os
import sys
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from .project_paths import PATHS
except ImportError:
    # For standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from project_paths import PATHS


class MigrationSafety:
    """Comprehensive safety system for file restructuring."""
    
    def __init__(self):
        """Initialize migration safety system."""
        self.project_root = PATHS.project_root
        self.backup_dir = self.project_root / "migration_backup" 
        self.cache_dirs = []
        self.metadata_backup = {}
        self.find_all_cache_dirs()
        
    def find_all_cache_dirs(self) -> List[Path]:
        """Find all __pycache__ directories in project."""
        cache_dirs = []
        for root, dirs, files in os.walk(self.project_root):
            if '__pycache__' in dirs:
                cache_path = Path(root) / '__pycache__'
                # Skip cache dirs in dump folder
                if 'dump' not in str(cache_path):
                    cache_dirs.append(cache_path)
        
        self.cache_dirs = cache_dirs
        return cache_dirs
        
    def clear_all_python_cache(self) -> Dict[str, int]:
        """Clear ALL Python cache to prevent stale imports."""
        results = {'directories_removed': 0, 'files_removed': 0}
        
        # Find and remove __pycache__ directories
        for cache_dir in self.cache_dirs:
            if cache_dir.exists():
                file_count = len(list(cache_dir.rglob('*.pyc')))
                shutil.rmtree(cache_dir)
                print(f"✅ Cleared cache: {cache_dir} ({file_count} files)")
                results['directories_removed'] += 1
                results['files_removed'] += file_count
                
        # Clear Python import cache for our modules
        if hasattr(sys, 'modules'):
            modules_to_remove = []
            for module_name in sys.modules.keys():
                if any(prefix in module_name for prefix in [
                    'pipeline_', 'schemas', 'direct_', 'ai_table_detector',
                    'intelligent_financial_merger', 'universal_consolidator',
                    'enterprise_output_manager', 'targeted_llm_extractor',
                    'schema_based_extractor', 'financial_table_extractor'
                ]):
                    modules_to_remove.append(module_name)
            
            for module in modules_to_remove:
                del sys.modules[module]
                
            print(f"✅ Cleared sys.modules cache: {len(modules_to_remove)} modules")
            results['modules_cleared'] = len(modules_to_remove)
                
        return results
        
    def backup_enterprise_metadata(self) -> Dict[str, Any]:
        """Backup all JSON manifests and metadata."""
        print("📋 Backing up enterprise metadata...")
        
        metadata_files = [
            PATHS.output_dir / "STATUS.json",
            PATHS.output_dir / "METADATA.json", 
            PATHS.output_dir / "RUN_SUMMARY.txt"
        ]
        
        # Create backup directory
        backup_metadata_dir = self.backup_dir / "metadata"
        backup_metadata_dir.mkdir(parents=True, exist_ok=True)
        
        backup_info = {'files_backed_up': [], 'run_directories': []}
        
        # Backup metadata files
        for file_path in metadata_files:
            if file_path.exists():
                backup_path = backup_metadata_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                backup_info['files_backed_up'].append(str(file_path))
                print(f"✅ Backed up: {file_path.name}")
                
        # Catalog run directories
        runs_dir = PATHS.output_dir / "runs"
        if runs_dir.exists():
            backup_info['run_directories'] = self._catalog_run_directories(runs_dir)
            
        # Save backup manifest
        backup_manifest = backup_metadata_dir / "backup_manifest.json"
        with open(backup_manifest, 'w') as f:
            json.dump(backup_info, f, indent=2, default=str)
            
        self.metadata_backup = backup_info
        print(f"✅ Enterprise metadata backup complete: {len(backup_info['files_backed_up'])} files")
        return backup_info
        
    def _catalog_run_directories(self, runs_dir: Path) -> List[Dict[str, Any]]:
        """Catalog all existing run directories and their contents."""
        runs = []
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir():
                files = []
                total_size = 0
                for file_path in run_dir.rglob("*"):
                    if file_path.is_file():
                        file_info = {
                            'path': str(file_path.relative_to(self.project_root)),
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                        files.append(file_info)
                        total_size += file_info['size']
                
                runs.append({
                    'directory': str(run_dir.relative_to(self.project_root)),
                    'files': files,
                    'file_count': len(files),
                    'total_size': total_size
                })
        return runs
        
    def verify_metadata_integrity(self) -> bool:
        """Verify all metadata is intact after migration."""
        print("🔍 Verifying metadata integrity...")
        
        issues = []
        
        # Check that all original metadata files still exist
        metadata_files = [
            PATHS.output_dir / "STATUS.json",
            PATHS.output_dir / "METADATA.json",
            PATHS.output_dir / "RUN_SUMMARY.txt"
        ]
        
        for file_path in metadata_files:
            if not file_path.exists():
                issues.append(f"Missing metadata file: {file_path}")
                
        # Check that run directories are still accessible
        if 'run_directories' in self.metadata_backup:
            for run_info in self.metadata_backup['run_directories']:
                run_path = self.project_root / run_info['directory']
                if not run_path.exists():
                    issues.append(f"Missing run directory: {run_path}")
                    
        if issues:
            print("❌ Metadata integrity issues found:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        else:
            print("✅ Metadata integrity verified")
            return True
            
    def create_rollback_point(self, phase_name: str) -> str:
        """Create a complete rollback point for the current phase."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rollback_id = f"{phase_name}_{timestamp}"
        
        rollback_dir = self.backup_dir / "rollback_points" / rollback_id
        rollback_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rollback information
        rollback_info = {
            'id': rollback_id,
            'phase': phase_name,
            'timestamp': timestamp,
            'project_root': str(self.project_root),
            'git_commit': self._get_current_git_commit(),
            'files_snapshot': self._create_files_snapshot()
        }
        
        # Save rollback info
        rollback_manifest = rollback_dir / "rollback_manifest.json"
        with open(rollback_manifest, 'w') as f:
            json.dump(rollback_info, f, indent=2, default=str)
            
        print(f"✅ Rollback point created: {rollback_id}")
        return rollback_id
        
    def _get_current_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
            
    def _create_files_snapshot(self) -> Dict[str, str]:
        """Create a snapshot of current file checksums."""
        snapshot = {}
        python_files = list(self.project_root.glob("*.py")) + list(self.project_root.glob("schemas/*.py"))
        
        for file_path in python_files:
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    snapshot[str(file_path.relative_to(self.project_root))] = file_hash
                    
        return snapshot
        
    def test_import_safety(self) -> Dict[str, Any]:
        """Test that critical imports still work after changes."""
        import_results = {'success': [], 'failed': []}
        
        # Test core imports that should always work
        critical_imports = [
            'main',
            'pipeline_logger', 
            'enterprise_output_manager',
            'schemas',
            'ai_table_detector'
        ]
        
        for import_name in critical_imports:
            try:
                __import__(import_name)
                import_results['success'].append(import_name)
                print(f"✅ Import test passed: {import_name}")
            except ImportError as e:
                import_results['failed'].append({'module': import_name, 'error': str(e)})
                print(f"❌ Import test failed: {import_name} - {e}")
                
        return import_results


class PathCompatibilityLayer:
    """Create compatibility for old path references during migration."""
    
    def __init__(self):
        self.compatibility_mappings = {}
        
    def create_import_aliases(self) -> Dict[str, str]:
        """Create import aliases for moved modules."""
        # This will be expanded during migration to handle moved files
        aliases = {
            # Old path -> New path mappings will be added here
        }
        return aliases


def run_pre_migration_safety_check():
    """Run comprehensive pre-migration safety check."""
    print("🚀 Starting Pre-Migration Safety Check")
    print("=" * 50)
    
    safety = MigrationSafety()
    
    # Step 1: Clear Python cache
    print("\n📁 Step 1: Clearing Python Cache")
    cache_results = safety.clear_all_python_cache()
    print(f"Cleared {cache_results['directories_removed']} cache directories, "
          f"{cache_results['files_removed']} files, "
          f"{cache_results.get('modules_cleared', 0)} modules")
    
    # Step 2: Backup enterprise metadata
    print("\n💾 Step 2: Backing Up Enterprise Metadata")
    metadata_backup = safety.backup_enterprise_metadata()
    
    # Step 3: Test current imports
    print("\n🔍 Step 3: Testing Current Import Safety")
    import_results = safety.test_import_safety()
    
    # Step 4: Create rollback point
    print("\n📋 Step 4: Creating Rollback Point")
    rollback_id = safety.create_rollback_point("pre_migration")
    
    # Summary
    print("\n✅ Pre-Migration Safety Check Complete")
    print("=" * 50)
    print(f"Cache cleared: {cache_results['directories_removed']} directories")
    print(f"Metadata backed up: {len(metadata_backup['files_backed_up'])} files")
    print(f"Imports successful: {len(import_results['success'])}/{len(import_results['success']) + len(import_results['failed'])}")
    print(f"Rollback point: {rollback_id}")
    
    if import_results['failed']:
        print("\n⚠️  Import failures detected:")
        for failure in import_results['failed']:
            print(f"  • {failure['module']}: {failure['error']}")
        return False
    
    return True


if __name__ == "__main__":
    # Run safety check
    success = run_pre_migration_safety_check()
    exit(0 if success else 1)