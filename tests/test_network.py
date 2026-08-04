import sys
from unittest.mock import MagicMock

# Cleanup mock dependencies to avoid side effects
del sys.modules["osint_nexus.core.browser"]
del sys.modules["osint_nexus.core.config"]
del sys.modules["osint_nexus.core.exceptions"]
del sys.modules["osint_nexus.core.evasion_agent"]
del sys.modules["osint_nexus.core.mimicry"]
del sys.modules["osint_nexus.utils.limiter"]
del sys.modules["osint_nexus.utils.retry"]
del sys.modules["curl_cffi.requests"]


import pytest

from osint_nexus.utils.network import NetworkMonitor


@pytest.fixture
def mock_config() -> MagicMock:
    config = MagicMock()
    config.http_timeout = 10.0
    return config


@pytest.fixture
def mock_evasion() -> MagicMock:
    from unittest.mock import AsyncMock

    evasion = MagicMock()
    evasion.report_failure = AsyncMock()
    return evasion


def test_network_monitor_adapt(mock_config: MagicMock, mock_evasion: MagicMock) -> None:
    monitor = NetworkMonitor(mock_config, mock_evasion)
    initial_timeout = monitor.dynamic_timeout

    # Test adaptation (response time > 80% of timeout)
    monitor.adapt(9.0)  # 9.0 > 8.0
    assert monitor.dynamic_timeout > initial_timeout


def test_network_monitor_handle_status(mock_config: MagicMock, mock_evasion: MagicMock) -> None:
    monitor = NetworkMonitor(mock_config, mock_evasion)
    initial_timeout = monitor.dynamic_timeout

    # Test handling of 429
    import asyncio

    asyncio.run(monitor.handle_status(429))

    mock_evasion.report_failure.assert_called_once_with(429)
    assert monitor.dynamic_timeout > initial_timeout
