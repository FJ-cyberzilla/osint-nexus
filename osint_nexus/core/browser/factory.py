from __future__ import annotations

import random
from typing import Any

try:
    from playwright.async_api import Browser, BrowserContext
except ImportError:
    Browser = Any
    BrowserContext = Any

# Import configuration from pool - need to be careful of circular dependencies
from osint_nexus.core.browser.config import BrowserPoolConfig

STEALTH_INIT_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    window.chrome = { runtime: {} };
"""


class BrowserContextFactory:
    """Handles configuration and creation of stealthy BrowserContexts."""

    def __init__(self, config: BrowserPoolConfig) -> None:
        self.config = config

    async def create(
        self, browser: Browser, proxy_url: str | None = None, extra_headers: dict[str, str] | None = None
    ) -> BrowserContext:
        """Configures and creates a new BrowserContext."""
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

        await context.add_init_script(STEALTH_INIT_SCRIPT)
        return context
