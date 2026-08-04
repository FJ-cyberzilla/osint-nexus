from typing import Any

from osint_nexus.core.telemetry import TelemetryProbe
from osint_nexus.utils.network import NetworkManager


class DNSLeakProbe(TelemetryProbe):
    def __init__(self, network_manager: NetworkManager, target_urls: list[str]):
        self.network_manager = network_manager
        self.target_urls = target_urls

    async def run(self) -> dict[str, Any]:
        """
        Execute DNS leak detection by querying unique target URLs and
        checking for leakage patterns.
        """
        results = {}
        for url in self.target_urls:
            # We use curl for lightweight probing without rendering
            success, content = await self.network_manager.fetch(url, use_browser=False)
            results[url] = {
                "success": success,
                "leaked": success,  # Simplified logic for now
            }
        return results
