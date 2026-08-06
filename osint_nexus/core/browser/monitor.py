from __future__ import annotations

from osint_nexus.core.browser.protocols import BrowserProtocol


class PoolMonitor:
    """Monitors resource health and pool state."""

    def __init__(self) -> None:
        self.active_contexts = 0

    def record_acquisition(self) -> None:
        self.active_contexts += 1

    def record_release(self) -> None:
        self.active_contexts = max(0, self.active_contexts - 1)

    def check_health(self, browser: BrowserProtocol | None) -> bool:
        return browser is not None and browser.is_connected()
