import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock dependencies to avoid circular imports
sys.modules["osint_nexus.core.browser"] = MagicMock()
sys.modules["osint_nexus.core.browser.factory"] = MagicMock()
sys.modules["osint_nexus.core.provider_runner"] = MagicMock()
sys.modules["osint_nexus.core.orchestrator"] = MagicMock()

from osint_nexus.core.evasion_agent import EvasionAgent  # noqa: E402
from osint_nexus.utils.network import NetworkManager, NetworkMonitor, SessionManager  # noqa: E402


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.http_timeout = 10.0
    config.TLS_PROFILES = ["chrome120"]
    config.user_agents = ["Mozilla/5.0"]
    config.retry_attempts = 3
    config.retry_delay = 0.1
    config.retry_backoff_factor = 1.0
    return config


@pytest.fixture
def mock_evasion():
    return MagicMock(spec=EvasionAgent)


# --- Test NetworkMonitor ---


def test_network_monitor_adapt(mock_config, mock_evasion):
    monitor = NetworkMonitor(mock_config, mock_evasion)
    initial_timeout = monitor.dynamic_timeout

    monitor.adapt(initial_timeout * 0.9)
    assert monitor.dynamic_timeout > initial_timeout

    new_timeout = monitor.dynamic_timeout
    monitor.adapt(initial_timeout * 0.1)
    assert monitor.dynamic_timeout == new_timeout


@pytest.mark.asyncio
async def test_network_monitor_handle_status(mock_config, mock_evasion):
    monitor = NetworkMonitor(mock_config, mock_evasion)

    await monitor.handle_status(403)
    mock_evasion.report_failure.assert_called_with(403)

    await monitor.handle_status(200)
    assert mock_evasion.report_failure.call_count == 1


# --- Test SessionManager ---


@pytest.mark.asyncio
async def test_session_manager_get_session(mock_config, mock_evasion):
    session_manager = SessionManager(mock_config, mock_evasion, 10.0)

    with patch("osint_nexus.utils.network.curl_requests.AsyncSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        session = await session_manager.get_session()
        assert session == mock_session
        assert session_manager._session is not None

        # Test reuse
        session2 = await session_manager.get_session()
        assert session2 == session
        assert mock_session_class.call_count == 1

        await session_manager.close()
        assert session_manager._session is None


# --- Test NetworkManager ---


@pytest.mark.asyncio
async def test_network_manager_fetch_curl(mock_config, mock_evasion):
    mock_mimicry = AsyncMock()
    mock_browser_pool = MagicMock()
    mock_rate_limiter = AsyncMock()

    manager = NetworkManager(mock_config, mock_evasion, mock_mimicry, mock_browser_pool, mock_rate_limiter)

    with patch.object(manager, "_fetch_http", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (True, "<html></html>")

        success, content = await manager.fetch("http://example.com")
        assert success is True
        assert content == "<html></html>"
        mock_fetch.assert_called_once()
