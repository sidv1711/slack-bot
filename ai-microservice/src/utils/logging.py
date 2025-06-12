"""Logging configuration for the AI Microservice."""
import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration for the AI microservice."""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    logging.info(f"🔧 Logging configured at {log_level} level") 