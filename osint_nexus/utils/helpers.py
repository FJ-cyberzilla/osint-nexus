"""
Logging configuration helpers for OSINT Nexus.

Provides centralized logging setup that reads from the project Config
and avoids duplicate handler registration.
"""

from __future__ import annotations

import logging
from pathlib import Path

from osint_nexus.core.config import Config

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

    log_path = _get_log_file_path(config, log_file)
    log_level = _get_log_level(config)
    _configure_root_logger(log_path, log_level)

    _logging_configured = True

    return logging.getLogger(logger_name)


def _get_log_file_path(config: Config | None, log_file: str | None) -> Path:
    if log_file:
        return Path(log_file)
    if config and config.db_path:
        return Path(config.db_path).parent / "osint.log"
    return Path("osint.log")


def _get_log_level(config: Config | None) -> int:
    if config and hasattr(config, "log_level"):
        return config.log_level
    return logging.INFO


def _configure_root_logger(log_path: Path, log_level: int) -> None:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
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
