import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from osint_nexus.core import bootstrap
from osint_nexus.core.config import Config
from osint_nexus.utils import helpers


@pytest.fixture(autouse=True)
def reset_logging() -> Generator[None]:
    """Reset the logging configuration flag before each test."""
    helpers._logging_configured = False
    # Also reset the root logger handlers to avoid side effects
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    yield
    helpers._logging_configured = False


def test_get_log_file_path() -> None:
    assert helpers._get_log_file_path(None) == bootstrap.LOGS_DIR / "osint.log"
    assert helpers._get_log_file_path("test.log") == bootstrap.LOGS_DIR / "test.log"


def test_get_log_level() -> None:
    assert helpers._get_log_level(None) == logging.INFO
    config = MagicMock(spec=Config)
    config.log_level = logging.DEBUG
    assert helpers._get_log_level(config) == logging.DEBUG


def test_setup_logger() -> None:
    with patch("osint_nexus.utils.helpers._configure_root_logger") as mock_configure:
        logger = helpers.setup_logger()
        assert logger.name == "osint_nexus"
        assert helpers._logging_configured is True
        mock_configure.assert_called_once()

        # Subsequent call should return same logger and not call configure again
        logger2 = helpers.setup_logger()
        assert logger is logger2
        assert mock_configure.call_count == 1


def test_configure_root_logger() -> None:
    # Smoke test to run through the function without errors
    helpers._configure_root_logger(bootstrap.LOGS_DIR / "test.log", logging.DEBUG)
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 2


def test_get_logger() -> None:
    logger = helpers.get_logger("test_module")
    assert logger.name == "test_module"
