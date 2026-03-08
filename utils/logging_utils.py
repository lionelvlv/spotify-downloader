"""
Logging utilities with colored console output and file logging.
"""
import logging
import sys
from pathlib import Path
from typing import Optional


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\033[90m'


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.GREY,
        logging.INFO: Colors.CYAN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.RED + Colors.BOLD,
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if record.levelno in self.LEVEL_COLORS:
            levelname_color = f"{self.LEVEL_COLORS[record.levelno]}{levelname}{Colors.RESET}"
            record.levelname = levelname_color
        
        # Format the message
        result = super().format(record)
        
        # Reset color
        record.levelname = levelname
        return result


def setup_logging(
    verbose: bool = False,
    log_file: Optional[Path] = None,
    name: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging with console and optional file output.
    
    Args:
        verbose: If True, set DEBUG level, otherwise INFO
        log_file: Optional path to log file
        name: Logger name (defaults to root logger)
        
    Returns:
        Configured logger instance
    """
    # Determine log level
    level = logging.DEBUG if verbose else logging.INFO
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (no colors)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for file
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class ProgressLogger:
    """Simple progress tracker for batch operations."""
    
    def __init__(self, total: int, logger: logging.Logger, prefix: str = "Progress"):
        self.total = total
        self.current = 0
        self.logger = logger
        self.prefix = prefix
        self.success = 0
        self.failed = 0
    
    def increment(self, success: bool = True):
        """Increment progress counter."""
        self.current += 1
        if success:
            self.success += 1
        else:
            self.failed += 1
    
    def log_progress(self, message: str = ""):
        """Log current progress."""
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        status = f"[{self.current}/{self.total}] ({percentage:.1f}%)"
        
        if message:
            self.logger.info(f"{self.prefix} {status}: {message}")
        else:
            self.logger.info(f"{self.prefix} {status}")
    
    def log_summary(self):
        """Log final summary."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Summary: {self.total} total, {self.success} succeeded, {self.failed} failed")
        self.logger.info(f"{'='*60}\n")
