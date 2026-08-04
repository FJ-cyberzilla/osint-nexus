from __future__ import annotations

from typing import Any

try:
    from playwright.async_api import Browser
except ImportError:
    Browser = Any


class PoolMonitor:
    """Monitors resource health and pool state."""

    def __init__(self) -> None:
        self.active_contexts = 0

    def record_acquisition(self) -> None:
        self.active_contexts += 1

    def record_release(self) -> None:
        self.active_contexts = max(0, self.active_contexts - 1)

    def check_health(self, browser: Browser | None) -> bool:
        return browser is not None and browser.is_connected()
