from unittest.mock import MagicMock

import pytest

from osint_nexus.utils.network import NetworkManager, NetworkMonitor, SessionManager


@pytest.mark.asyncio
async def test_session_manager_init():
    config = MagicMock()
    evasion = MagicMock()
    sm = SessionManager(config, evasion, 30.0)
    assert sm.dynamic_timeout == 30.0


def test_network_monitor_adapt():
    config = MagicMock()
    config.http_timeout = 10.0
    evasion = MagicMock()

    nm = NetworkMonitor(config, evasion)
    nm.adapt(9.0)  # > 0.8 * 10
    assert nm.dynamic_timeout > 10.0


@pytest.mark.asyncio
async def test_network_manager_init():
    config = MagicMock()
    evasion = MagicMock()
    mimicry = MagicMock()
    browser_pool = MagicMock()

    nm = NetworkManager(config, evasion, mimicry, browser_pool)
    assert nm.config == config
