import sys
from unittest.mock import MagicMock

import pytest

# Mock dependencies that cause circular imports
sys.modules["osint_nexus.core.browser"] = MagicMock()
sys.modules["osint_nexus.core.browser.factory"] = MagicMock()

from osint_nexus.core.config import Config  # noqa: E402
from osint_nexus.core.evasion_agent import EvasionAgent  # noqa: E402
from osint_nexus.utils.network import NetworkMonitor  # noqa: E402


@pytest.fixture
def mock_config() -> MagicMock:
    config = MagicMock(spec=Config)
    config.http_timeout = 10.0
    return config


@pytest.fixture
def mock_evasion() -> MagicMock:
    return MagicMock(spec=EvasionAgent)


def test_network_monitor_adapt(mock_config: MagicMock, mock_evasion: MagicMock) -> None:
    monitor = NetworkMonitor(mock_config, mock_evasion)
    initial_timeout = monitor.dynamic_timeout

    # Test adapt with long response time
    monitor.adapt(initial_timeout * 0.9)
    assert monitor.dynamic_timeout > initial_timeout

    # Test adapt with short response time (no change)
    new_timeout = monitor.dynamic_timeout
    monitor.adapt(initial_timeout * 0.1)
    assert monitor.dynamic_timeout == new_timeout


@pytest.mark.asyncio
async def test_network_monitor_handle_status(mock_config: MagicMock, mock_evasion: MagicMock) -> None:
    monitor = NetworkMonitor(mock_config, mock_evasion)

    # Test 403
    await monitor.handle_status(403)
    mock_evasion.report_failure.assert_called_with(403)

    # Test 200 (no action)
    await monitor.handle_status(200)
    assert mock_evasion.report_failure.call_count == 1
