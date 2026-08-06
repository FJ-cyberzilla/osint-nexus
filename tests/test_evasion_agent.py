from unittest.mock import MagicMock, patch

import pytest

from osint_nexus.core.evasion_agent import EvasionAgent


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.user_agents = ["UA1"]
    return config


@pytest.mark.asyncio
async def test_evasion_agent_init(mock_config):
    agent = EvasionAgent(mock_config)
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = "proxy:123"
        mock_get.return_value = mock_resp

        await agent.initialize()
        assert agent.get_proxy() == "proxy:123"


@pytest.mark.asyncio
async def test_evasion_agent_health_check(mock_config):
    mock_config.require_proxy = False
    agent = EvasionAgent(mock_config)
    assert await agent.health_check() is True
