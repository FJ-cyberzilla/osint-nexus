from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum, auto
from types import TracebackType
from typing import Any, Self

try:
    from playwright.async_api import (
        Browser,
        BrowserContext,
        Playwright,
        async_playwright,
    )
    from playwright.async_api import (
        Error as PlaywrightError,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    BrowserContext = Any
    Playwright = Any
    async_playwright = Any
    PlaywrightError = Exception

from osint_nexus.core.browser.config import BrowserPoolConfig
from osint_nexus.core.browser.factory import BrowserContextFactory
from osint_nexus.core.browser.monitor import PoolMonitor
from osint_nexus.core.telemetry.bridge import WebViewBridge

logger = logging.getLogger("osint_nexus.core.browser.pool")


class BrowserPoolError(Exception):
    """Base exception for BrowserPoolManager failures."""

    pass


class BrowserPoolState(Enum):
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    CLOSED = auto()


class BrowserPoolManager:
    """
    Manages a pool of hardened browser contexts safely and concurrently.
    """

    def __init__(self, config: BrowserPoolConfig | None = None, bridge: WebViewBridge | None = None) -> None:
        self.config = config or BrowserPoolConfig()
        self._factory = BrowserContextFactory(self.config)
        self._monitor = PoolMonitor()
        self._bridge = bridge
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._state: BrowserPoolState = BrowserPoolState.UNINITIALIZED
        self._lifecycle_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initializes the Playwright daemon and Chromium browser thread-safely."""
        if not PLAYWRIGHT_AVAILABLE:
            raise BrowserPoolError("Playwright is not installed.")

        async with self._lifecycle_lock:
            if self._state == BrowserPoolState.READY:
                return

            self._state = BrowserPoolState.INITIALIZING
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.config.headless, args=["--disable-blink-features=AutomationControlled"]
                )
                self._state = BrowserPoolState.READY
            except Exception as e:
                await self._force_cleanup()
                raise BrowserPoolError(f"Initialization failed: {e}") from e

    @asynccontextmanager
    async def acquire_context(
        self, proxy_url: str | None = None, extra_headers: dict[str, str] | None = None
    ) -> AsyncGenerator[BrowserContext]:
        """Acquires a hardened browser context using the factory."""
        if self._state != BrowserPoolState.READY:
            await self.initialize()

        if not self._monitor.check_health(self._browser):
            self._state = BrowserPoolState.UNINITIALIZED
            await self.initialize()

        context: BrowserContext | None = None
        try:
            context = await self._factory.create(
                self._browser, proxy_url=proxy_url, extra_headers=extra_headers
            )
            if self._bridge:
                # Expose the bridge handler to the page
                page = context.pages[0] if context.pages else await context.new_page()
                await page.expose_function("webviewBridge", self._bridge.handle_message)

            self._monitor.record_acquisition()
            yield context
        except PlaywrightError as e:
            raise BrowserPoolError(f"Context error: {e}") from e
        finally:
            if context:
                await context.close()
                self._monitor.record_release()

    async def close(self) -> None:
        """Gracefully closes the browser and stops the Playwright daemon."""
        async with self._lifecycle_lock:
            if self._state == BrowserPoolState.CLOSED:
                return
            await self._force_cleanup()

    async def _force_cleanup(self) -> None:
        """Internal teardown routine bypassing the lock."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        finally:
            self._browser = None
            self._playwright = None
            self._state = BrowserPoolState.CLOSED

    async def __aenter__(self) -> Self:
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
