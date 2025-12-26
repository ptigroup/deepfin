"""
Core Infrastructure Module
Project paths, migration safety, cross-platform compatibility, and foundational systems.
"""

from .project_paths import PATHS, ensure_project_context
from .migration_safety import MigrationSafety, run_pre_migration_safety_check
from .cross_platform_paths import CrossPlatformPaths, run_cross_platform_compatibility_check
from .pipeline_logger import logger
from .pipeline_01_2_enterprise_manager import EnterpriseOutputManager