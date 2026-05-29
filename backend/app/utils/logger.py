"""
utils/logger.py
───────────────
Centralised structured logging factory.

Design:
- One function `get_logger(name)` returns a configured logger
- Format includes timestamp, level, module name, and message
- Log level is driven by settings so it can be changed via .env
"""

import logging
import sys
from app.config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with a consistent format.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the same logger is requested twice
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent log records from propagating to the root logger (avoids duplicates)
    logger.propagate = False

    return logger
