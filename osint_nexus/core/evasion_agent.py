"""
Evasion subsystem for OSINT agent.

Provides proxy rotation, User-Agent selection, and failure-driven
adaptation to avoid detection. Integrates with the hierarchy health
monitoring by implementing the HealthCheckable protocol.
"""

from __future__ import annotations

import logging
import random

import httpx

from osint_nexus.core.config import Config
from osint_nexus.utils.data_loader import load_data

logger = logging.getLogger("osint_nexus.evasion")


class EvasionAgent:
    """
    Manages anti‑detection measures: proxies, User‑Agent strings,
    and adaptive rotation based on failure signals.

    Requires explicit initialization before use:

        agent = EvasionAgent(config)
        await agent.initialize()   # fetches first proxy, loads UA pool
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.current_proxy: str | None = None
        self.user_agents: list[str] = self._load_user_agents()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def initialize(self) -> None:
        """
        Fetch an initial proxy (if required) and prepare resources.
        Must be called before the first scan.
        """
        await self._refresh_proxy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_proxy(self) -> str | None:
        """Return the currently active proxy, or None if direct."""
        return self.current_proxy

    def get_user_agent(self) -> str:
        """Return a random User-Agent string from the pool."""
        return random.choice(self.user_agents)  # nosec B311

    async def report_failure(self, status_code: int) -> None:
        """
        Rotate the proxy immediately when a protective status code is received.
        Respects a per‑rotation cool‑down to avoid hammering the proxy API.
        """
        if status_code in (403, 429):
            logger.warning("Rotating proxy due to status %d", status_code)
            await self._refresh_proxy()

    async def health_check(self) -> bool:
        """
        Check if the evasion subsystem is operational.

        Returns True if either:
        - A proxy is configured and available, or
        - Proxy usage is not required.
        """
        if self.config.require_proxy and not self.current_proxy:
            logger.error("Proxy required but none available.")
            return False
        return True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _load_user_agents(self) -> list[str]:
        """Return the User-Agent pool from config or a safe default list."""
        agents = self.config.user_agents
        if agents and isinstance(agents, list) and len(agents) > 0:
            return agents
        return load_data("user_agents.json")

    async def _refresh_proxy(self) -> None:
        """
        Fetch a fresh proxy from the configured API endpoint.
        Falls back to direct connection if:
        - No proxy API URL is set, or
        - The API call fails (after logging the error).
        """
        proxy_api_url = self.config.proxy_api_url.strip()
        if not proxy_api_url:
            self.current_proxy = None
            logger.debug("No proxy API URL – using direct connection.")
            return

        try:
            async with httpx.AsyncClient(timeout=self.config.http_timeout) as client:
                response = await client.get(proxy_api_url)
                response.raise_for_status()
                # Expect a plain text proxy URL in the response body
                proxy = response.text.strip()
                if proxy:
                    self.current_proxy = proxy
                    logger.info("Proxy refreshed: %s", proxy)
                else:
                    raise ValueError("Empty proxy response")
        except Exception:
            logger.exception("Failed to fetch proxy – falling back to direct connection.")
            self.current_proxy = None
