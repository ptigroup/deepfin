#!/usr/bin/env python3
"""
Pipeline Logger - Environment-Aware Logging System

Provides clean, professional output for production use while preserving
detailed debugging capabilities for audit mode.

Usage:
    from pipeline_logger import logger
    
    # Basic logging
    logger.info("Processing started")
    logger.success("Operation completed")
    logger.error("Operation failed")
    
    # Progress bars
    with logger.progress("Processing PDF 1/2: document.pdf") as progress:
        progress.update(25, "AI detecting tables...")
        progress.update(75, "Extracting data...")
        progress.complete("5 tables extracted")
        
    # Debug (only in audit mode)
    logger.debug("Detailed debug information")
"""

import os
import sys
import time
import logging
from typing import Optional, Any
from contextlib import contextmanager

# Configure logging suppression for production mode
def setup_production_logging():
    """Setup logging configuration for production mode."""
    if os.getenv('MODE', 'production').lower() == 'production':
        # Suppress all LLMWhisperer logging in production
        for logger_name in ['unstract.llmwhisperer.client_v2', 'unstract.llmwhisperer', 'unstract']:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).disabled = True
        
        # Set root logger to WARNING to suppress debug messages
        logging.basicConfig(level=logging.WARNING)

# Apply production logging setup immediately
setup_production_logging()


class GlobalProgressTracker:
    """Single progress tracker for the entire pipeline."""
    
    def __init__(self, width: int = 20):
        self.width = width
        self.start_time = time.time()
        self.current_percent = 0
        self.current_stage = ""
        self.stages = {
            'input_discovery': (0, 10, 'Input Discovery'),
            'pdf1_processing': (10, 45, 'Processing PDF 1/2'),
            'pdf2_processing': (45, 80, 'Processing PDF 2/2'),  
            'consolidation': (80, 95, 'Multi-PDF Consolidation'),
            'final_output': (95, 100, 'Final Output')
        }
        
    def update_stage(self, stage_key: str, stage_progress: int = 0, activity: str = ""):
        """Update progress for a specific pipeline stage."""
        if stage_key not in self.stages:
            return
            
        start_percent, end_percent, stage_name = self.stages[stage_key]
        
        # Calculate overall progress
        stage_range = end_percent - start_percent
        stage_contribution = (stage_progress / 100) * stage_range
        self.current_percent = min(100, start_percent + stage_contribution)
        
        # Format timing
        elapsed = time.time() - self.start_time
        
        # Create progress bar
        filled = int(self.width * self.current_percent / 100)
        bar = "█" * filled + "▓" * (self.width - filled)
        
        # Display progress
        stage_display = f"{stage_name}"
        if activity:
            stage_display += f" - {activity}"
        
        # Create the line and ensure it clears any leftover text
        line = f"[{bar}] {self.current_percent:3.0f}% {stage_display} ({elapsed:.0f}s)"
        
        # Clear the entire line first, then print our content
        print(f"\r{' ' * 120}", end="", flush=True)  # Clear with spaces
        print(f"\r{line}", end="", flush=True)       # Print our content
    
    def complete(self, final_message: str = ""):
        """Mark entire pipeline as complete."""
        elapsed = time.time() - self.start_time
        filled_bar = "█" * self.width
        
        if final_message:
            line = f"[{filled_bar}] 100% Complete - {final_message} ({elapsed:.0f}s)"
        else:
            line = f"[{filled_bar}] 100% Pipeline completed in {elapsed:.0f}s"
        
        # Clear the line first, then print final result with newline
        print(f"\r{' ' * 120}", end="", flush=True)  # Clear with spaces
        print(f"\r{line}")                           # Print final line with newline


class ProgressBar:
    """Simple progress bar for console output."""
    
    def __init__(self, description: str, width: int = 20):
        self.description = description
        self.width = width
        self.start_time = time.time()
        self.current_percent = 0
        self.current_activity = ""
        
    def update(self, percent: int, activity: str = ""):
        """Update progress bar with percentage and activity description."""
        self.current_percent = min(100, max(0, percent))
        self.current_activity = activity
        
        # Create progress bar
        filled = int(self.width * self.current_percent / 100)
        bar = "█" * filled + "▓" * (self.width - filled)
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        
        # Format the line
        if activity:
            line = f"  [{bar}] {self.current_percent:3d}% {activity} ({elapsed:.0f}s)"
        else:
            line = f"  [{bar}] {self.current_percent:3d}% ({elapsed:.0f}s)"
        
        # Print with carriage return to overwrite
        print(f"\r{line}", end="", flush=True)
        
    def complete(self, final_message: str = ""):
        """Complete the progress bar with final message."""
        elapsed = time.time() - self.start_time
        bar = "█" * self.width
        
        if final_message:
            line = f"  [{bar}] 100% Complete - {final_message} ({elapsed:.0f}s)"
        else:
            line = f"  [{bar}] 100% Complete ({elapsed:.0f}s)"
            
        print(f"\r{line}")


class PipelineLogger:
    """Environment-aware logger for the financial document processing pipeline."""
    
    def __init__(self):
        """Initialize logger with mode detection."""
        self.mode = os.getenv('MODE', 'production').lower()
        self._is_production = self.mode == 'production'
        self.global_progress = GlobalProgressTracker()
        
    def _should_log_debug(self) -> bool:
        """Determine if debug-level messages should be printed."""
        return not self._is_production
        
    def info(self, message: str, prefix: str = "ℹ️  "):
        """Log informational messages (always visible)."""
        print(f"{prefix}{message}")
        
    def success(self, message: str):
        """Log success messages (always visible)."""
        self.info(message, prefix="✅ ")
        
    def warning(self, message: str):
        """Log warning messages (always visible)."""
        self.info(message, prefix="⚠️  ")
        
    def error(self, message: str):
        """Log error messages (always visible)."""
        self.info(message, prefix="❌ ")
        
    def debug(self, message: str, prefix: str = "🔍 "):
        """Log debug messages (audit mode only)."""
        if self._should_log_debug():
            print(f"{prefix}{message}")
            
    def debug_detailed(self, message: str, prefix: str = "    DEBUG "):
        """Log detailed debug messages (audit mode only)."""
        if self._should_log_debug():
            print(f"{prefix}{message}")
            
    def section_header(self, title: str):
        """Print a section header."""
        if self._should_log_debug():
            print(f"\n{'='*60}")
            print(f"{title.upper()}")
            print(f"{'='*60}")
        else:
            print(f"\n🚀 {title}")
            print("=" * 60)
            
    def pipeline_header(self):
        """Print the main pipeline header."""
        self.section_header("Financial Document Processing Pipeline")
        
    @contextmanager
    def progress(self, description: str):
        """Context manager for progress bar operations."""
        if self._is_production:
            # Show progress bar in production
            print(f"\n📄 {description}")
            progress_bar = ProgressBar(description)
            
            class ProgressContext:
                def update(self, percent: int, activity: str = ""):
                    progress_bar.update(percent, activity)
                    
                def complete(self, final_message: str = ""):
                    progress_bar.complete(final_message)
                    
            yield ProgressContext()
        else:
            # In audit mode, just print the description and yield a no-op context
            print(f"\n📄 {description}")
            
            class NoOpProgress:
                def update(self, percent: int, activity: str = ""):
                    if activity:
                        logger.debug(f"Progress {percent}%: {activity}")
                        
                def complete(self, final_message: str = ""):
                    if final_message:
                        logger.success(final_message)
                        
            yield NoOpProgress()
            
    def processing_summary(self, run_id: str, duration: float, output_file: str, warnings: int = 0):
        """Print the final processing summary."""
        print(f"\n🎉 Pipeline Complete!")
        self.success(f"Run {run_id} completed in {duration:.1f}s")
        print(f"📁 Output: {output_file}")
        if warnings > 0:
            self.warning(f"{warnings} consolidation warning{'s' if warnings != 1 else ''} - individual files available")


# Global logger instance
logger = PipelineLogger()


def main():
    """Test the logger functionality."""
    print("Testing Pipeline Logger")
    print("=" * 40)
    
    # Test basic logging
    logger.info("This is an info message")
    logger.success("This is a success message")  
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.debug("This is a debug message (audit mode only)")
    logger.debug_detailed("This is detailed debug (audit mode only)")
    
    # Test section header
    logger.section_header("Test Section")
    
    # Test progress bar
    with logger.progress("Testing progress bar") as progress:
        import time
        progress.update(25, "Starting process...")
        time.sleep(1)
        progress.update(50, "Processing data...")
        time.sleep(1) 
        progress.update(75, "Finalizing...")
        time.sleep(1)
        progress.complete("Test completed successfully")
        
    # Test summary
    logger.processing_summary("test_12345", 156.7, "test_output.xlsx", 1)


if __name__ == "__main__":
    main()