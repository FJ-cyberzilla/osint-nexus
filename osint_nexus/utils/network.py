"""
Robust HTTP client with built-in evasion, retry, and TLS impersonation.

This module provides a NetworkManager that handles persistent session state,
proxy integration, and browser-grade TLS fingerprinting.
"""

from __future__ import annotations

import logging
import random
from typing import Any, cast

import curl_cffi.requests as curl_requests
import httpx

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.utils.retry import RetryHandler

logger = logging.getLogger("osint_nexus.network")


class NetworkManager:
    """
    Manages HTTP request lifecycles with evasion, retry, and persistent TLS sessions.

    This class serves as the central hub for all network operations, ensuring
    that proxy rotation and browser fingerprinting remain consistent across
    the duration of an OSINT investigation.
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

    def _get_session(self) -> curl_requests.AsyncSession:
        """
        Retrieves or initializes a persistent curl_cffi session.

        The session is bound to a single TLS profile and proxy for the duration
        of its lifecycle to prevent detection via fingerprint inconsistencies.
        """
        new_proxy = self.evasion.get_proxy()

        if self._session is None or new_proxy != self._current_proxy:
            profiles = getattr(self.config, "TLS_PROFILES", ["chrome120"])
            self._current_profile = random.choice(profiles)
            self._current_proxy = new_proxy

            self._session = curl_requests.AsyncSession(
                impersonate=cast(Any, self._current_profile), proxy=self._current_proxy
            )
            logger.debug("Created new session with profile %s", self._current_profile)

        return self._session

    async def fetch(self, url: str, headers: dict[str, str] | None = None, use_browser: bool = False, **browser_options: Any) -> tuple[bool, str]:
        """
        Performs a GET request using the configured evasion and retry logic, with dynamic User-Agent support.

        Args:
            url: The destination URL.
            headers: Optional custom headers to use.
            use_browser: If True, uses the local BrowserPool headless browser.
            **browser_options: Keyword arguments for browser parameters.

        Returns:
            A tuple of (success_boolean, response_text).
        """

        async def _attempt() -> tuple[bool, str]:
            await self.mimicry.apply_jitter()

            if use_browser:
                return await self._fetch_with_browser(url, **browser_options)

            session = self._get_session()
            
            # Build request headers
            request_headers = {"Referer": "https://www.google.com/"}
            if headers:
                request_headers.update(headers)
            
            # Inject dynamic User-Agent if not provided
            if "User-Agent" not in request_headers:
                request_headers["User-Agent"] = random.choice(self.config.user_agents)

            try:
                response = await session.get(url, headers=request_headers, timeout=self.config.http_timeout)
                await self._handle_response_status(response.status_code)
                is_success: bool = response.status_code == 200
                response_text: str = str(response.text)
                result: tuple[bool, str] = (is_success, response_text)
                return result
            except (curl_requests.RequestsError, httpx.HTTPError) as exc:
                logger.error("Request failed: %s", exc)
                self._session = None
                raise

        try:
            result: tuple[bool, str] = await self.retry.run(_attempt)
            return result
        except (curl_requests.RequestsError, httpx.HTTPError):
            logger.exception("Request failed after retries: %s", url)
            await self.close_session()
            error_result: tuple[bool, str] = (False, "")
            return error_result

    async def _fetch_with_browser(self, url: str, **browser_options: Any) -> tuple[bool, str]:
        """
        Executes a request via the local BrowserPool.
        """
        context = await self.browser_pool.get_context()
        page = await context.new_page()
        try:
            response = await page.goto(url, timeout=int(self.config.http_timeout * 1000))
            content = await page.content()
            return (response is not None and response.status == 200, content)
        finally:
            await context.close()

    async def _handle_response_status(self, status_code: int) -> None:
        """
        Evaluates HTTP response status and rotates sessions on blockages.

        Args:
            status_code: The HTTP status code received.
        """
        if status_code in (403, 429):
            logger.warning("Protective status code %s detected.", status_code)
            self._session = None
            await self.evasion.report_failure(status_code)

    async def close_session(self) -> None:
        """Explicitly closes the active session and clears state."""
        if self._session:
            await self._session.close()
            self._session = None
