#!/usr/bin/env python3
"""
Centralized Path Management System
Prevents relative path issues during and after refactoring by providing
absolute path resolution from any execution context.
"""

import os
import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Optional


class ProjectPaths:
    """Centralized path management to prevent relative path issues during refactoring."""
    
    def __init__(self):
        """Initialize with project root detection."""
        # Always resolve to project root regardless of where code is executed from
        self.project_root = self._get_safe_project_root()
        
        # Core directories (unchanged during refactoring)
        self.input_dir = self.project_root / "input"
        self.output_dir = self.project_root / "output" 
        self.schemas_dir = self.project_root / "schemas"
        self.temp_dir = self.project_root / "temp"
        self.config_file = self.project_root / ".env"
        self.dump_dir = self.project_root / "dump"
        
        # New structure directories (created during refactoring)
        self.core_dir = self.project_root / "core"
        self.tests_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"
        
        # Pipeline directories (created during refactoring)
        self.pipeline_01_dir = self.project_root / "pipeline_01_input_discovery"
        self.pipeline_02_dir = self.project_root / "pipeline_02_table_detection"
        self.pipeline_03_dir = self.project_root / "pipeline_03_extraction"
        self.pipeline_04_dir = self.project_root / "pipeline_04_processing"
        self.pipeline_05_dir = self.project_root / "pipeline_05_consolidation"
        
        # WSL2 compatibility detection
        self.is_wsl = self._detect_wsl()
        
    def _detect_wsl(self) -> bool:
        """Detect if running in WSL environment."""
        try:
            return 'microsoft' in platform.uname().release.lower()
        except:
            return False
            
    def _get_safe_project_root(self) -> Path:
        """Get project root that works in WSL2 and Windows."""
        # Find the project root by looking for key marker files
        current = Path(__file__).parent.parent  # Go up from /core/ to project root
        
        # Verify this is actually the project root by checking for key files
        marker_files = ['main.py', 'CLAUDE.md', 'schemas']
        if all((current / marker).exists() for marker in marker_files):
            return current.resolve()
        else:
            # Fallback: search upward from current location
            search_path = Path.cwd()
            for _ in range(5):  # Search up to 5 levels
                if all((search_path / marker).exists() for marker in marker_files):
                    return search_path.resolve()
                search_path = search_path.parent
            
            # Final fallback
            return Path.cwd().resolve()
            
    def get_relative_to_root(self, path: str) -> Path:
        """Convert any relative path to be relative to project root."""
        # Clean path separators for cross-platform compatibility
        clean_path = str(path).replace('\\', '/')
        return self.project_root / clean_path
        
    def ensure_directories(self):
        """Ensure all necessary directories exist with proper permissions."""
        directories = [
            self.input_dir, self.output_dir, self.temp_dir,
            self.core_dir, self.tests_dir, self.docs_dir,
            self.pipeline_01_dir, self.pipeline_02_dir, self.pipeline_03_dir,
            self.pipeline_04_dir, self.pipeline_05_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Test write access
            self._test_directory_access(directory)
            
    def _test_directory_access(self, directory: Path):
        """Test that directory is writable."""
        test_file = directory / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            print(f"WARNING: Cannot write to {directory}: {e}")
            
    def safe_path(self, relative_path: str) -> Path:
        """Convert any path to be safe for current environment."""
        return self.get_relative_to_root(relative_path)
        
    def get_current_working_context(self) -> dict:
        """Get information about current execution context."""
        return {
            'current_dir': Path.cwd(),
            'project_root': self.project_root,
            'is_wsl': self.is_wsl,
            'platform': platform.system(),
            'python_executable': Path(os.sys.executable)
        }


# Global instance - import this everywhere instead of using relative paths
PATHS = ProjectPaths()


def ensure_project_context():
    """Ensure we're operating from correct project context."""
    # Change working directory to project root if not already there
    if Path.cwd().resolve() != PATHS.project_root:
        os.chdir(PATHS.project_root)
        print(f"Changed working directory to project root: {PATHS.project_root}")
    
    # Ensure all directories exist
    PATHS.ensure_directories()


if __name__ == "__main__":
    # Test the path management system
    print("=== Project Paths Test ===")
    context = PATHS.get_current_working_context()
    for key, value in context.items():
        print(f"{key}: {value}")
    
    print(f"\nProject structure:")
    print(f"Input dir: {PATHS.input_dir}")
    print(f"Output dir: {PATHS.output_dir}")
    print(f"Schemas dir: {PATHS.schemas_dir}")
    print(f"Core dir: {PATHS.core_dir}")
    
    # Test directory creation
    PATHS.ensure_directories()
    print("\n✅ All directories verified/created successfully")