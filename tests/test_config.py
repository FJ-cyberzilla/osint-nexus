import pytest
import os
import json
from osint_nexus.core.config import Config

def test_config_from_env_basic():
    """Test basic environment variable parsing."""
    os.environ["OSINT_HTTP_TIMEOUT"] = "100"
    os.environ["OSINT_REQUIRE_PROXY"] = "true"
    
    config = Config.from_env()
    
    assert config.http_timeout == 100
    assert config.require_proxy is True
    
    # Clean up
    del os.environ["OSINT_HTTP_TIMEOUT"]
    del os.environ["OSINT_REQUIRE_PROXY"]

def test_config_from_env_json_list():
    """Test environment variable parsing for list types (JSON)."""
    # Using a valid JSON string for a list
    os.environ["OSINT_USER_AGENTS"] = '["Mozilla/5.0", "Mozilla/6.0"]'
    
    config = Config.from_env()
    
    assert len(config.user_agents) == 2
    assert config.user_agents[0] == "Mozilla/5.0"
    
    # Clean up
    del os.environ["OSINT_USER_AGENTS"]

def test_config_from_env_invalid_json():
    """Test handling of invalid JSON in environment variables."""
    # This should trigger the warning in Config.from_env
    os.environ["OSINT_USER_AGENTS"] = 'invalid-json'
    
    # We expect this to not raise an exception, just log a warning based on current impl
    config = Config.from_env()
    
    # Should keep the default
    assert len(config.user_agents) > 0
    
    # Clean up
    del os.environ["OSINT_USER_AGENTS"]
