"""
Robust HTTP client with built-in evasion, retry, and TLS impersonation.

This module provides an advanced NetworkManager that handles persistent session state,
safe concurrent proxy rotation, browser-grade TLS fingerprinting, and dynamic 
environment adaptation for OSINT intelligence gathering.
"""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType
from typing import Any, cast, Self

import curl_cffi.requests as curl_requests

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.utils.retry import RetryHandler

logger = logging.getLogger("osint_nexus.network")


class NetworkManagerError(Exception):
    """Base exception for network operations."""
    pass


class NetworkManager:
    """
    Manages HTTP request lifecycles with evasion, retry, and persistent TLS sessions.

    Features:
    - Async thread-safe session rotation.
    - Automatic environment and network profiling.
    - Context-manager driven connection cleanup.
    - Graceful degradation between curl_cffi and headless browsers.
    """

    def __init__(
        self,
        config: Config,
        evasion: EvasionAgent,
        mimicry: HumanMimicryEngine,
        browser_pool: BrowserPoolManager,
    ) -> None:
        self.config = config
        self.evasion = evasion
        self.mimicry = mimicry
        self.browser_pool = browser_pool
        self.retry = RetryHandler(config)

        # Session state
        self._session: curl_requests.AsyncSession | None = None
        self._current_proxy: str | None = None
        self._current_profile: str | None = None
        
        # Concurrency safety for session rotation
        self._session_lock = asyncio.Lock()
        
        # Environment adaptation state
        self._dynamic_timeout: float = self.config.http_timeout

    async def _get_session(self) -> curl_requests.AsyncSession:
        """
        Retrieves or initializes a persistent curl_cffi session safely.
        Uses an asyncio.Lock to prevent race conditions during proxy rotation
        in highly concurrent scan scenarios.
        """
        new_proxy = self.evasion.get_proxy()

        async with self._session_lock:
            # If session is dead or proxy mandates a rotation
            if self._session is None or new_proxy != self._current_proxy:
                if self._session is not None:
                    # Prevent socket leaks by explicitly closing the old session
                    await self._session.close()

                profiles = getattr(self.config, "TLS_PROFILES", ["chrome120", "edge114", "safari15_3"])
                self._current_profile = random.choice(profiles)
                self._current_proxy = new_proxy

                self._session = curl_requests.AsyncSession(
                    impersonate=cast(Any, self._current_profile),
                    proxy=self._current_proxy,
                    timeout=self._dynamic_timeout
                )
                logger.debug(
                    "Initialized new TLS session [Profile: %s | Proxy: %s]", 
                    self._current_profile, 
                    "Active" if self._current_proxy else "Direct"
                )

            return self._session

    def _adapt_to_environment(self, response_time: float = 0.0) -> None:
        """
        Automatically tunes network parameters based on environment telemetry.
        E.g., Backs off timeouts if proxies are generally slow.
        """
        if response_time > (self._dynamic_timeout * 0.8):
            # Scale timeout up gently if we are approaching the ceiling
            new_timeout = min(self._dynamic_timeout * 1.5, self.config.http_timeout * 2.5)
            if new_timeout != self._dynamic_timeout:
                logger.debug("Environment adaptation: Scaling HTTP timeout to %.2fs", new_timeout)
                self._dynamic_timeout = new_timeout

    async def fetch(
        self, 
        url: str, 
        headers: dict[str, str] | None = None, 
        use_browser: bool = False, 
        **browser_options: Any
    ) -> tuple[bool, str]:
        """
        Performs a GET request using the configured evasion and retry logic.

        Args:
            url: The destination URL.
            headers: Optional custom headers.
            use_browser: If True, uses the local BrowserPool headless browser.
            **browser_options: Keyword arguments for browser parameters.

        Returns:
            A tuple of (success_boolean, response_text).
        """
        async def _attempt() -> tuple[bool, str]:
            await self.mimicry.apply_jitter()

            if use_browser:
                return await self._fetch_with_browser(url, **browser_options)
            
            return await self._fetch_with_curl(url, headers)

        try:
            return await self.retry.run(_attempt)
        except Exception as exc:
            logger.error("Request totally failed after all retries for %s: %s", url, exc)
            # Ensure the broken session is flagged for recreation
            await self._invalidate_session()
            return False, ""

    async def _fetch_with_curl(self, url: str, custom_headers: dict[str, str] | None) -> tuple[bool, str]:
        """Executes the HTTP request via curl_cffi with impersonation."""
        session = await self._get_session()
        
        # Case-insensitive header construction
        request_headers = {
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # Merge custom headers without overwriting them accidentally
        if custom_headers:
            request_headers.update(custom_headers)
        
        # Inject dynamic User-Agent only if strictly required / not handled by impersonate
        if "User-Agent" not in request_headers and hasattr(self.config, "user_agents"):
            request_headers["User-Agent"] = random.choice(self.config.user_agents)

        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await session.get(
                url, 
                headers=request_headers, 
                timeout=self._dynamic_timeout
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            self._adapt_to_environment(elapsed)
            
            await self._handle_response_status(response.status_code)
            
            is_success = response.status_code in (200, 201, 204)
            return is_success, str(response.text)
            
        except curl_requests.RequestsError as exc:
            logger.warning("cURL request error to %s: %s", url, exc)
            await self._invalidate_session()
            raise NetworkManagerError(f"cURL failure: {exc}") from exc

    async def _fetch_with_browser(self, url: str, **browser_options: Any) -> tuple[bool, str]:
        """Executes a request via the local BrowserPool ensuring strict memory boundaries."""
        try:
            context = await self.browser_pool.get_context()
        except Exception as e:
            logger.error("Failed to acquire browser context: %s", e)
            raise NetworkManagerError("Browser pool exhausted or dead.") from e

        try:
            page = await context.new_page()
            # Dynamic timeout conversion for Playwright/Puppeteer (milliseconds)
            timeout_ms = int(self._dynamic_timeout * 1000)
            
            response = await page.goto(url, timeout=timeout_ms, **browser_options)
            content = await page.content()
            
            # None response usually means a navigation to a non-HTTP target (like about:blank) 
            # or an intercepted request.
            is_success = response is not None and response.status == 200
            
            if response:
                await self._handle_response_status(response.status)
                
            return is_success, content
            
        except Exception as exc:
            logger.warning("Browser navigation failed for %s: %s", url, exc)
            raise NetworkManagerError(f"Browser failure: {exc}") from exc
        finally:
            # Guarantee the context is closed to free up the RAM/Pool slot
            await context.close()

    async def _handle_response_status(self, status_code: int) -> None:
        """
        Evaluates HTTP response status and coordinates with the Evasion Engine.
        """
        if status_code in (403, 429, 401, 407):
            logger.warning("Protective or blocking status code %s detected.", status_code)
            await self._invalidate_session()
            await self.evasion.report_failure(status_code)
            
            # Automatically apply a cooldown penalty to the environment timeout
            self._dynamic_timeout = min(self._dynamic_timeout * 1.2, self.config.http_timeout * 3)

    async def _invalidate_session(self) -> None:
        """Thread-safe teardown of the current session so it gets rebuilt on next request."""
        async with self._session_lock:
            if self._session:
                await self._session.close()
                self._session = None

    async def close_all(self) -> None:
        """Explicitly closes the active session and clears state gracefully."""
        await self._invalidate_session()

    # --- Async Context Manager Protocol ---
    
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, 
        exc_type: type[BaseException] | None, 
        exc_val: BaseException | None, 
        exc_tb: TracebackType | None
    ) -> None:
        """Ensures all network connections are severed when exiting scope."""
        await self.close_all()
