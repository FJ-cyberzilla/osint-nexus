"""
Local Browser Pool Manager using Playwright.

Provides hardened, evasion-capable browser contexts for deep parsing and
complex scraping tasks, replacing reliance on external headless APIs.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    BrowserContext = Any
    Playwright = Any
    async_playwright = Any

logger = logging.getLogger("osint_nexus.core.browser")


class BrowserPoolManager:
    """
    Manages a pool of hardened browser contexts.
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def initialize(self) -> None:
        """Initializes the browser pool."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed or not supported on this platform.")

        if not self._playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            logger.info("Browser pool initialized.")

    async def get_context(self) -> BrowserContext:
        """Creates a new hardened context."""
        if not self._browser:
            await self.initialize()

        # We know self._browser is not None here because initialize() ensures it.
        # However, for mypy strictness:
        browser = self._browser
        if browser is None:
            raise RuntimeError("Browser failed to initialize.")

        # In a production-hardened scenario, this would apply stealth plugins
        # or specific user-agent/fingerprint configurations.
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        return context

    async def close(self) -> None:
        """Closes the pool."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser pool closed.")
