"""
Logging configuration for the application.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

from app.config import get_settings


class CustomFormatter(logging.Formatter):
    """Custom formatter adding colors to the logs."""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging() -> None:
    """
    Set up the logging configuration for the application.
    """
    settings = get_settings()
    
    # Get log level from settings
    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    
    # Set specific levels for some loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Log setup completion
    logging.info(f"Logging configured with level: {log_level_str}")
