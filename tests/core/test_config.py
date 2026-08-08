import os
from unittest.mock import patch

from osint_nexus.core.config import Config


def test_config_from_env_basic() -> None:
    """Test basic environment variable parsing."""
    with patch.dict(os.environ, {"OSINT_HTTP_TIMEOUT": "100", "OSINT_REQUIRE_PROXY": "true"}):
        config = Config.from_env()

        assert config.http_timeout == 100
        assert config.require_proxy is True


def test_config_from_env_json_list() -> None:
    """Test environment variable parsing for list types (JSON)."""
    # Using a valid JSON string for a list
    with patch.dict(os.environ, {"OSINT_USER_AGENTS": '["Mozilla/5.0", "Mozilla/6.0"]'}):
        config = Config.from_env()

        assert len(config.user_agents) == 2
        assert config.user_agents[0] == "Mozilla/5.0"


def test_config_from_env_invalid_json() -> None:
    """Test handling of invalid JSON in environment variables."""
    # This should trigger the warning in Config.from_env
    with patch.dict(os.environ, {"OSINT_USER_AGENTS": "invalid-json"}):
        # We expect this to not raise an exception, just log a warning based on current impl
        config = Config.from_env()

        # Should keep the default
        assert len(config.user_agents) > 0
