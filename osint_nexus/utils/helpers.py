"""
Logging configuration helpers for OSINT Nexus.

Provides centralized logging setup that reads from the project Config
and avoids duplicate handler registration.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from osint_nexus.core.config import Config

# Global flag to prevent multiple root handler setup
_logging_configured: bool = False


def setup_logger(
    config: Optional[Config] = None,
    log_file: Optional[str] = None,
    logger_name: str = "osint_nexus",
) -> logging.Logger:
    """
    Configure root logging and return a named logger.

    Only runs once per process; subsequent calls return the same
    configured logger without adding duplicate handlers.

    Args:
        config: Optional Config instance. Uses ``db_path`` to derive
            log file path and ``log_level`` for verbosity (INFO default).
        log_file: Path to log file. Overrides any value derived from config.
        logger_name: Name of the logger to return (default 'osint_nexus').

    Returns:
        A configured logger instance.
    """
    global _logging_configured  # noqa: PLW0603 (global statement)

    if _logging_configured:
        return logging.getLogger(logger_name)

    # Determine log file path
    resolved_log_file = log_file
    if not resolved_log_file and config:
        # Use the database directory with a default name
        db_path = Path(config.db_path) if config.db_path else Path(".")
        resolved_log_file = str(db_path.parent / "osint.log")
    if not resolved_log_file:
        resolved_log_file = "osint.log"

    # Determine log level
    log_level = logging.INFO
    if config and hasattr(config, "log_level"):
        log_level = config.log_level

    # Build formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(Path(resolved_log_file))
    file_handler.setFormatter(formatter)

    # Stream handler (console)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    _logging_configured = True

    return logging.getLogger(logger_name)


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger with the given name.

    This is the preferred way to obtain loggers in other modules;
    it does not reconfigure logging and relies on `setup_logger`
    having been called once at application startup.
    """
    return logging.getLogger(name)
