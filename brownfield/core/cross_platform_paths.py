#!/usr/bin/env python3
"""
Cross-Platform Path Management
Handles WSL2, Windows, and Linux path compatibility issues during refactoring.
"""

import os
import platform
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Optional, Dict, Any, List

try:
    from .project_paths import PATHS
except ImportError:
    # For standalone execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from project_paths import PATHS


class CrossPlatformPaths:
    """Handle WSL2 and cross-platform path issues during migration."""
    
    def __init__(self):
        """Initialize cross-platform path management."""
        self.platform_info = self._detect_platform()
        self.project_root = PATHS.project_root
        self.path_separators = self._get_path_separators()
        
    def _detect_platform(self) -> Dict[str, Any]:
        """Detect current platform and environment details."""
        system = platform.system().lower()
        
        platform_info = {
            'system': system,
            'is_windows': system == 'windows',
            'is_linux': system == 'linux', 
            'is_wsl': False,
            'is_wsl2': False,
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0]
        }
        
        # Detect WSL specifically
        if system == 'linux':
            try:
                # Check for WSL in kernel release
                kernel_release = platform.release().lower()
                if 'microsoft' in kernel_release or 'wsl' in kernel_release:
                    platform_info['is_wsl'] = True
                    
                    # Check for WSL2 specifically
                    if 'wsl2' in kernel_release or self._is_wsl2():
                        platform_info['is_wsl2'] = True
                        
            except Exception:
                pass
                
        return platform_info
        
    def _is_wsl2(self) -> bool:
        """Check if running under WSL2 specifically."""
        try:
            # WSL2 uses a different kernel than WSL1
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                return 'microsoft' in version and 'wsl2' in version
        except:
            return False
            
    def _get_path_separators(self) -> Dict[str, str]:
        """Get appropriate path separators for current platform."""
        if self.platform_info['is_windows']:
            return {'native': '\\', 'universal': '/'}
        else:
            return {'native': '/', 'universal': '/'}
            
    def normalize_path(self, path_str: str) -> Path:
        """Normalize path for current platform."""
        # Convert all separators to universal forward slashes
        normalized = str(path_str).replace('\\', '/')
        
        # Handle Windows drive letters in WSL
        if self.platform_info['is_wsl'] and ':' in normalized:
            # Convert Windows paths like C:/... to /mnt/c/...
            if normalized[1:3] == ':/':
                drive_letter = normalized[0].lower()
                rest_of_path = normalized[3:]
                normalized = f"/mnt/{drive_letter}/{rest_of_path}"
                
        return Path(normalized)
        
    def safe_path_conversion(self, path: Path) -> Path:
        """Convert path to be safe for current environment."""
        try:
            # Resolve to absolute path
            abs_path = path.resolve()
            
            # Test that path is accessible
            if abs_path.exists():
                return abs_path
            else:
                # Try to create parent directories if they don't exist
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                return abs_path
                
        except Exception as e:
            print(f"⚠️  Path conversion warning for {path}: {e}")
            return path
            
    def test_path_compatibility(self) -> Dict[str, Any]:
        """Test path compatibility for current environment."""
        print("🧪 Testing path compatibility...")
        
        test_results = {
            'platform_info': self.platform_info,
            'project_root_accessible': False,
            'input_dir_accessible': False,
            'output_dir_accessible': False,
            'temp_dir_writable': False,
            'path_length_limit': None,
            'case_sensitivity': None
        }
        
        # Test project root accessibility
        try:
            list(self.project_root.iterdir())
            test_results['project_root_accessible'] = True
            print("✅ Project root accessible")
        except Exception as e:
            print(f"❌ Project root not accessible: {e}")
            
        # Test input directory
        if PATHS.input_dir.exists():
            test_results['input_dir_accessible'] = True
            print("✅ Input directory accessible")
        else:
            print("⚠️  Input directory not found")
            
        # Test output directory
        if PATHS.output_dir.exists():
            test_results['output_dir_accessible'] = True
            print("✅ Output directory accessible")
        else:
            print("⚠️  Output directory not found")
            
        # Test temp directory writability
        test_results['temp_dir_writable'] = self._test_directory_writable(PATHS.temp_dir)
        
        # Test path length limits
        test_results['path_length_limit'] = self._test_path_length_limit()
        
        # Test case sensitivity
        test_results['case_sensitivity'] = self._test_case_sensitivity()
        
        return test_results
        
    def _test_directory_writable(self, directory: Path) -> bool:
        """Test if directory is writable."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            test_file = directory / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            print(f"✅ Directory writable: {directory}")
            return True
        except Exception as e:
            print(f"❌ Directory not writable {directory}: {e}")
            return False
            
    def _test_path_length_limit(self) -> Optional[int]:
        """Test maximum path length for current platform."""
        if self.platform_info['is_windows']:
            # Windows has 260 character limit (unless long paths enabled)
            return 260
        else:
            # Unix-like systems typically have 4096 character limit
            return 4096
            
    def _test_case_sensitivity(self) -> bool:
        """Test if filesystem is case sensitive."""
        try:
            test_dir = PATHS.temp_dir / "case_test"
            test_dir.mkdir(exist_ok=True)
            
            # Create lowercase file
            lower_file = test_dir / "test.txt"
            lower_file.write_text("lower")
            
            # Try to create uppercase file
            upper_file = test_dir / "TEST.txt"
            
            if lower_file.exists() and not upper_file.exists():
                # Filesystem is case sensitive
                upper_file.write_text("upper")
                case_sensitive = upper_file.exists() and lower_file.read_text() == "lower"
            else:
                # Filesystem is case insensitive
                case_sensitive = False
                
            # Cleanup
            if lower_file.exists():
                lower_file.unlink()
            if upper_file.exists():
                upper_file.unlink()
            test_dir.rmdir()
            
            print(f"📁 Filesystem case sensitive: {case_sensitive}")
            return case_sensitive
            
        except Exception as e:
            print(f"⚠️  Could not determine case sensitivity: {e}")
            return True  # Assume case sensitive for safety
            
    def get_platform_specific_recommendations(self) -> List[str]:
        """Get recommendations for current platform."""
        recommendations = []
        
        if self.platform_info['is_wsl2']:
            recommendations.extend([
                "Running in WSL2: File operations may be slower across Windows/Linux boundary",
                "Consider keeping all files in Linux filesystem for best performance",
                "Be aware of case sensitivity differences between Windows and Linux"
            ])
            
        if self.platform_info['is_windows']:
            recommendations.extend([
                "Windows detected: Watch for path length limits (260 chars)",
                "Use forward slashes in paths for cross-platform compatibility"
            ])
            
        if not self._test_directory_writable(PATHS.temp_dir):
            recommendations.append("Temp directory not writable - check permissions")
            
        return recommendations
        
    def create_safe_symlinks(self, source: Path, target: Path) -> bool:
        """Create symbolic links safely across platforms."""
        try:
            # Remove existing symlink/file
            if target.exists() or target.is_symlink():
                target.unlink()
                
            # Create symlink
            if self.platform_info['is_windows']:
                # Windows requires admin rights for symlinks, use junction instead
                subprocess.run(['mklink', '/J', str(target), str(source)], 
                             shell=True, check=True)
            else:
                # Unix-like systems
                target.symlink_to(source)
                
            print(f"✅ Created symlink: {target} -> {source}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create symlink {target} -> {source}: {e}")
            return False


def run_cross_platform_compatibility_check():
    """Run comprehensive cross-platform compatibility check."""
    print("🌐 Cross-Platform Compatibility Check")
    print("=" * 40)
    
    cross_platform = CrossPlatformPaths()
    
    # Test platform compatibility
    test_results = cross_platform.test_path_compatibility()
    
    # Show platform info
    print(f"\n📋 Platform Information:")
    platform_info = test_results['platform_info']
    print(f"  System: {platform_info['system']}")
    print(f"  WSL: {platform_info['is_wsl']}")
    print(f"  WSL2: {platform_info['is_wsl2']}")
    print(f"  Python: {platform_info['python_version']}")
    print(f"  Architecture: {platform_info['architecture']}")
    
    # Show test results
    print(f"\n🧪 Compatibility Test Results:")
    print(f"  Project root accessible: {'✅' if test_results['project_root_accessible'] else '❌'}")
    print(f"  Input dir accessible: {'✅' if test_results['input_dir_accessible'] else '❌'}")
    print(f"  Output dir accessible: {'✅' if test_results['output_dir_accessible'] else '❌'}")
    print(f"  Temp dir writable: {'✅' if test_results['temp_dir_writable'] else '❌'}")
    print(f"  Path length limit: {test_results['path_length_limit']} chars")
    print(f"  Case sensitive: {test_results['case_sensitivity']}")
    
    # Show recommendations
    recommendations = cross_platform.get_platform_specific_recommendations()
    if recommendations:
        print(f"\n💡 Platform-Specific Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")
    
    # Determine if safe to proceed
    critical_issues = [
        not test_results['project_root_accessible'],
        not test_results['temp_dir_writable']
    ]
    
    if any(critical_issues):
        print("\n❌ Critical compatibility issues found - migration may not be safe")
        return False
    else:
        print("\n✅ Platform compatibility check passed")
        return True


if __name__ == "__main__":
    # Run compatibility check
    success = run_cross_platform_compatibility_check()
    exit(0 if success else 1)