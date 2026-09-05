from unittest.mock import AsyncMock, MagicMock

import pytest

from osint_nexus.core.telemetry.probes.dns_leak import DNSLeakProbe
from osint_nexus.utils.network import NetworkManager


@pytest.mark.asyncio
async def test_dns_leak_probe():
    # Mock NetworkManager
    mock_network = MagicMock(spec=NetworkManager)
    # Mock fetch to return success
    mock_network.fetch = AsyncMock(return_value=(True, "<html></html>"))

    urls = ["http://leaktest.com"]
    probe = DNSLeakProbe(mock_network, urls)

    results = await probe.run()

    assert "http://leaktest.com" in results.keys()
    assert results["http://leaktest.com"]["success"] is True
    assert results["http://leaktest.com"]["is_reachable"] is True
    mock_network.fetch.assert_called_once_with("http://leaktest.com", use_browser=False)
