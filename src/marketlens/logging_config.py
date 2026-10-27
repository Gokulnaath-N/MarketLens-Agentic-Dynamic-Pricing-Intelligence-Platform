"""Logging configuration module for MarketLens AI.

Provides idempotent initialization of console and file loggers using Python's
standard library logging package, ensuring clean timestamp formatting and
avoiding duplicate handler accumulation.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TextIO

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str | int | None = None,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    stream: TextIO | None = None,
    force: bool = False,
) -> logging.Logger:
    """Initialize or update application-wide logging configuration.

    This function is idempotent by default: if root logger handlers already
    exist and force=False, it adjusts log levels without adding duplicate handlers.

    Args:
        level: Logging level (e.g., 'INFO', 'DEBUG', logging.INFO).
               Defaults to MARKETLENS_LOG_LEVEL environment variable or 'INFO'.
        log_format: Format string for log messages.
        date_format: Date format string for timestamps.
        stream: Output stream for console handler (defaults to sys.stderr).
        force: If True, existing handlers on the root logger are cleared and recreated.

    Returns:
        The configured root logger instance.

    Example:
        >>> from marketlens.logging_config import configure_logging
        >>> logger = configure_logging("INFO")
        >>> logger.info("MarketLens AI logging initialized.")
    """
    if level is None:
        level_str = os.getenv("MARKETLENS_LOG_LEVEL", "INFO").upper()
    elif isinstance(level, int):
        level_str = logging.getLevelName(level)
    else:
        level_str = str(level).upper()

    numeric_level = getattr(logging, level_str, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # If force is requested, clear existing handlers
    if force:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

    # Check if a StreamHandler is already present
    has_stream_handler = any(
        isinstance(h, logging.StreamHandler) for h in root_logger.handlers
    )

    if not has_stream_handler:
        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
        console_handler = logging.StreamHandler(stream=stream or sys.stderr)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    else:
        # Update existing handlers to the new level
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Convenience factory to obtain a named logger for a module.

    Args:
        name: Usually `__name__` of the calling module.

    Returns:
        A Logger instance with the given name.
    """
    return logging.getLogger(name)
