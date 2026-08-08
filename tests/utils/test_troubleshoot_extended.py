from unittest.mock import MagicMock, patch

from osint_nexus.utils.troubleshoot import setup_logging, troubleshoot_agent_error


def test_troubleshoot_agent_error_timeout():
    error = TimeoutError("Connection timed out")
    tip = troubleshoot_agent_error(error, provider_name="GitHub")
    assert "timed out" in tip
    assert "GitHub" in tip


def test_troubleshoot_agent_error_unknown():
    error = ValueError("Something unexpected")
    tip = troubleshoot_agent_error(error, provider_name="Unknown")
    assert "Unexpected error" in tip


def test_setup_logging():
    with patch("osint_nexus.utils.troubleshoot.logging.getLogger") as mock_get_logger:
        root_logger = MagicMock()
        mock_get_logger.return_value = root_logger

        setup_logging(verbose=True)
        assert root_logger.setLevel.called
        assert root_logger.handlers.clear.called
