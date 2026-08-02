"""
Logging configuration helpers for OSINT Nexus.

Provides centralized logging setup that reads from the project Config
and avoids duplicate handler registration.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler

from osint_nexus.core.config import LOGS_DIR, Config

# Global flag to prevent multiple root handler setup
_logging_configured: bool = False


def setup_logger(
    config: Config | None = None,
    log_file: str | None = None,
    logger_name: str = "osint_nexus",
) -> logging.Logger:
    """
    Configure root logging and return a named logger.

    Only runs once per process; subsequent calls return the same
    configured logger without adding duplicate handlers.

    Args:
        config: Optional Config instance. Uses ``log_level`` for verbosity (INFO default).
        log_file: Path to log file. Overrides any default value.
        logger_name: Name of the logger to return (default 'osint_nexus').

    Returns:
        A configured logger instance.
    """
    global _logging_configured  # noqa: PLW0603 (global statement)

    if _logging_configured:
        return logging.getLogger(logger_name)

    log_path = _get_log_file_path(log_file)
    log_level = _get_log_level(config)
    _configure_root_logger(log_path, log_level)

    _logging_configured = True

    return logging.getLogger(logger_name)


def _get_log_file_path(log_file: str | None) -> Path:
    if log_file:
        return Path(log_file)
    return LOGS_DIR / "osint.log"


def _get_log_level(config: Config | None) -> int:
    if config and hasattr(config, "log_level"):
        return config.log_level
    return logging.INFO


def _configure_root_logger(log_path: Path, log_level: int) -> None:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Use RichHandler for console logging
    stream_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_path=False,
        omit_repeated_times=True,
    )
    stream_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger with the given name.

    This is the preferred way to obtain loggers in other modules;
    it does not reconfigure logging and relies on `setup_logger`
    having been called once at application startup.
    """
    return logging.getLogger(name)
