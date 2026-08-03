"""
Local Browser Pool Manager using Playwright.

Provides hardened, evasion-capable browser contexts for deep parsing and
complex scraping tasks. Designed for concurrency, strict memory management,
and stealth to replace reliance on external headless APIs.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
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

logger = logging.getLogger("osint_nexus.core.browser")

# Basic stealth script to bypass simplistic bot detection (e.g., removing the webdriver flag)
STEALTH_INIT_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    window.chrome = { runtime: {} };
"""


class BrowserPoolError(Exception):
    """Base exception for BrowserPoolManager failures."""

    pass


@dataclass(frozen=True, slots=True)
class BrowserPoolConfig:
    """Immutable configuration for the browser pool and its contexts."""

    headless: bool = True
    timeout_ms: int = 30000
    user_agents: tuple[str, ...] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    )
    viewports: tuple[dict[str, int], ...] = field(
        default_factory=lambda: (
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1440, "height": 900},
        )
    )


class BrowserContextFactory:
    """Handles configuration and creation of stealthy BrowserContexts."""

    def __init__(self, config: BrowserPoolConfig) -> None:
        self.config = config

    async def create(
        self, browser: Browser, proxy_url: str | None = None, extra_headers: dict[str, str] | None = None
    ) -> BrowserContext:
        """Configures and creates a new BrowserContext."""
        # Randomize fingerprint
        user_agent = random.choice(self.config.user_agents)  # nosec B311
        viewport = random.choice(self.config.viewports)  # nosec B311
        proxy_config = {"server": proxy_url} if proxy_url else None

        context = await browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            proxy=proxy_config,
            extra_http_headers=extra_headers,
            bypass_csp=True,
        )

        # Inject stealth script
        await context.add_init_script(STEALTH_INIT_SCRIPT)
        return context


class BrowserPoolState(Enum):
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    READY = auto()
    CLOSED = auto()


class BrowserPoolManager:
    """
    Manages a pool of hardened browser contexts safely and concurrently.
    """

    def __init__(self, config: BrowserPoolConfig | None = None) -> None:
        self.config = config or BrowserPoolConfig()
        self._factory = BrowserContextFactory(self.config)
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._state: BrowserPoolState = BrowserPoolState.UNINITIALIZED

        # Guard for concurrent initialization requests
        self._lifecycle_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initializes the Playwright daemon and Chromium browser thread-safely."""
        if not PLAYWRIGHT_AVAILABLE:
            raise BrowserPoolError(
                "Playwright is not installed. Install via `pip install playwright` "
                "and run `playwright install chromium`."
            )

        async with self._lifecycle_lock:
            if self._state == BrowserPoolState.READY:
                return

            if self._state == BrowserPoolState.INITIALIZING:
                # Should not happen with proper locking/usage, but handle it
                raise BrowserPoolError("Initialization already in progress.")

            self._state = BrowserPoolState.INITIALIZING
            logger.debug("Initializing local Playwright browser pool...")
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.config.headless, args=["--disable-blink-features=AutomationControlled"]
                )
                self._state = BrowserPoolState.READY
                logger.info("Browser pool initialized successfully.")
            except Exception as e:
                logger.error("Failed to initialize Playwright: %s", e)
                await self._force_cleanup()
                raise BrowserPoolError(f"Initialization failed: {e}") from e

    @asynccontextmanager
    async def acquire_context(
        self, proxy_url: str | None = None, extra_headers: dict[str, str] | None = None
    ) -> AsyncGenerator[BrowserContext]:
        """
        Acquires a hardened browser context using the factory.
        """
        if not self._browser:
            await self.initialize()

        if self._browser is None:
            raise BrowserPoolError("Browser failed to initialize.")

        context: BrowserContext | None = None
        try:
            context = await self._factory.create(
                self._browser, proxy_url=proxy_url, extra_headers=extra_headers
            )

            logger.debug("Acquired hardened context (Proxy: %s)", "Yes" if proxy_url else "No")
            yield context

        except PlaywrightError as e:
            logger.error("Playwright error during context execution: %s", e)
            raise BrowserPoolError(f"Context error: {e}") from e
        finally:
            if context:
                await context.close()
                logger.debug("Released browser context (Memory freed).")

    async def close(self) -> None:
        """Gracefully closes the browser and stops the Playwright daemon."""
        async with self._lifecycle_lock:
            if self._state == BrowserPoolState.CLOSED:
                return
            await self._force_cleanup()

    async def _force_cleanup(self) -> None:
        """Internal teardown routine bypassing the lock."""
        logger.debug("Cleaning up browser pool resources...")
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning("Error during browser pool teardown: %s", e)
        finally:
            self._browser = None
            self._playwright = None
            self._state = BrowserPoolState.CLOSED
            logger.info("Browser pool closed.")

    # --- Async Context Manager Protocol ---

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
