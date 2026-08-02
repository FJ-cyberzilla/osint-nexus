"""
Advanced OSINT Browser Agent Engine using Playwright.

Features:
- True concurrent connection pooling via Semaphores to prevent OOM.
- Military-grade JS fingerprint evasion (WebGL, Plugins, Hardware).
- Dynamic Network Interception (drops media/fonts for 10x speed).
- Agentic human-mimicry capabilities for lazy-loaded SPAs.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Self

try:
    from playwright.async_api import (
        Browser,
        BrowserContext,
        Page,
        Playwright,
        Request,
        Route,
        async_playwright,
        Error as PlaywrightError,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    BrowserContext = Any
    Page = Any
    Playwright = Any
    Request = Any
    Route = Any
    async_playwright = Any
    PlaywrightError = Exception

logger = logging.getLogger("osint_nexus.core.browser")

# ==============================================================================
# ADVANCED STEALTH PAYLOAD
# Bypasses common fingerprinting by masking webdriver, spoofing WebGL,
# faking plugins, and randomizing hardware concurrency.
# ==============================================================================
ADVANCED_STEALTH_SCRIPT = """
    // 1. Erase webdriver footprint
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    
    // 2. Mock Chrome runtime
    window.chrome = { runtime: {}, app: {}, csid: {}, loadTimes: function() {} };
    
    // 3. Spoof Plugins to look like a real desktop browser
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
        ]
    });
    
    // 4. Randomize Hardware/Memory to prevent distinct fingerprinting
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => Math.floor(Math.random() * (16 - 4 + 1)) + 4 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => Math.floor(Math.random() * (16 - 4 + 1)) + 4 });
    
    // 5. Mask WebGL Renderer (often used to detect headless servers)
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) return 'Intel Inc.';
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter(parameter);
    };
"""


class BrowserAgentError(Exception):
    """Base exception for Browser Engine failures."""
    pass


@dataclass(frozen=True, slots=True)
class BrowserPoolConfig:
    """Immutable configuration for the advanced browser engine."""
    headless: bool = True
    timeout_ms: int = 45000
    max_concurrent_contexts: int = 10  # TRUE POOLING: Prevents memory exhaustion
    block_heavy_media: bool = True     # 10x speed boost by dropping images/CSS/fonts
    
    user_agents: tuple[str, ...] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    )
    viewports: tuple[dict[str, int], ...] = field(
        default_factory=lambda: (
            {"width": 1920, "height": 1080},
            {"width": 1440, "height": 900},
            {"width": 1536, "height": 864},
        )
    )
    locales: tuple[str, ...] = ("en-US", "en-GB", "en-AU", "en-CA")
    timezones: tuple[str, ...] = ("America/New_York", "Europe/London", "Australia/Sydney")


class BrowserPoolManager:
    """
    Elite OSINT Browser Engine.
    Manages bounded concurrency, network interception, and stealth fingerprinting.
    """

    def __init__(self, config: BrowserPoolConfig | None = None) -> None:
        self.config = config or BrowserPoolConfig()
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        
        # Lifecycle lock for safe daemon startup/shutdown
        self._lifecycle_lock = asyncio.Lock()
        
        # Concurrency Semaphore: The core of the "Pool"
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_contexts)

    async def initialize(self) -> None:
        """Initializes the Playwright daemon and Chromium engine safely."""
        if not PLAYWRIGHT_AVAILABLE:
            raise BrowserAgentError("Playwright is missing. Run `playwright install chromium`.")

        async with self._lifecycle_lock:
            if self._playwright and self._browser:
                return

            logger.debug("Booting advanced Playwright engine...")
            try:
                self._playwright = await async_playwright().start()
                
                # Hardened launch arguments to strip automation flags
                args = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                ]
                
                self._browser = await self._playwright.chromium.launch(
                    headless=self.config.headless,
                    args=args
                )
                logger.info(
                    "Browser Engine initialized [Max Concurrency: %d]", 
                    self.config.max_concurrent_contexts
                )
            except Exception as e:
                logger.error("Engine failure: %s", e)
                await self._force_cleanup()
                raise BrowserAgentError(f"Initialization failed: {e}") from e

    async def _route_interceptor(self, route: Route, request: Request) -> None:
        """
        Dynamically aborts non-essential network requests.
        Massively reduces proxy bandwidth usage and speeds up page load times.
        """
        if self.config.block_heavy_media and request.resource_type in {"image", "media", "font", "stylesheet"}:
            await route.abort()
        else:
            await route.continue_()

    @asynccontextmanager
    async def acquire_context(
        self, 
        proxy_url: str | None = None,
        extra_headers: dict[str, str] | None = None
    ) -> AsyncGenerator[BrowserContext, None]:
        """
        Acquires a hardened browser context from the pool queue.
        Waits asynchronously if the maximum concurrent contexts are in use.
        """
        if not self._browser:
            await self.initialize()

        if self._browser is None:
            raise BrowserAgentError("Browser engine is dead.")

        # Queue request if pool is full (TRUE POOLING)
        async with self._semaphore:
            
            # Dynamic Blending Profile
            user_agent = random.choice(self.config.user_agents)
            viewport = random.choice(self.config.viewports)
            locale = random.choice(self.config.locales)
            timezone = random.choice(self.config.timezones)
            proxy_config = {"server": proxy_url} if proxy_url else None

            context: BrowserContext | None = None
            try:
                context = await self._browser.new_context(
                    user_agent=user_agent,
                    viewport=viewport,
                    proxy=proxy_config,
                    extra_http_headers=extra_headers,
                    locale=locale,
                    timezone_id=timezone,
                    permissions=["geolocation"],  # Pre-grant common permissions to avoid prompts
                    bypass_csp=True, 
                )
                
                # 1. Inject Stealth Payload
                await context.add_init_script(ADVANCED_STEALTH_SCRIPT)
                
                # 2. Attach Network Interceptor (Bandwidth Saver)
                await context.route("**/*", self._route_interceptor)
                
                logger.debug(
                    "Acquired stealth context (Locale: %s | TZ: %s | Proxy: %s)", 
                    locale, timezone, "Yes" if proxy_url else "No"
                )
                yield context
                
            except PlaywrightError as e:
                logger.error("Playwright error during context execution: %s", e)
                raise BrowserAgentError(f"Context error: {e}") from e
            finally:
                if context:
                    await context.close()
                    logger.debug("Released browser context back to pool (Memory freed).")

    async def humanize_page(self, page: Page) -> None:
        """
        Agentic Behavior: Simulates human scrolling and interaction.
        Vital for triggering lazy-loaded JSON APIs on SPA targets (Instagram, TikTok).
        """
        logger.debug("Agent applying human-mimicry scrolling...")
        
        # Simulate initial read delay
        await page.wait_for_timeout(random.randint(500, 1500))
        
        # Natural multi-step scroll down
        for _ in range(random.randint(2, 4)):
            scroll_amount = random.randint(300, 800)
            await page.mouse.wheel(0, scroll_amount)
            await page.wait_for_timeout(random.randint(400, 1200))
            
        # Slight scroll back up (human correction)
        await page.mouse.wheel(0, -random.randint(100, 300))
        await page.wait_for_timeout(random.randint(300, 800))

    async def close(self) -> None:
        """Gracefully shuts down the browser engine."""
        async with self._lifecycle_lock:
            await self._force_cleanup()

    async def _force_cleanup(self) -> None:
        """Internal teardown routine."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning("Error during engine teardown: %s", e)
        finally:
            self._browser = None
            self._playwright = None
            logger.info("Browser Engine offline.")

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
