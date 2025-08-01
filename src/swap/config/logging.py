"""Logging configuration."""

import logging
import sys
from typing import Dict, Any

from rich.logging import RichHandler


def setup_logging(log_level: str = "INFO", debug: bool = False) -> None:
    """Setup application logging with rich formatting."""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                show_path=debug,
                show_time=True,
                markup=True,
            )
        ],
    )
    
    # Reduce noise from Google API client
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Set SQLAlchemy logging
    if debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)
