"""
Robust HTTP client with built-in evasion, retry, and TLS impersonation.

This module provides a NetworkManager that handles persistent session state,
proxy integration, and browser-grade TLS fingerprinting.
"""

from __future__ import annotations

import logging
import random
from typing import Any, cast

import curl_cffi.requests as curl_requests  # type: ignore
import httpx

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
    ) -> None:
        self.config = config
        self.evasion = evasion
        self.mimicry = mimicry
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
                impersonate=self._current_profile, proxy=self._current_proxy
            )
            logger.debug("Created new session with profile %s", self._current_profile)

        return self._session

    async def fetch(self, url: str, use_microlink: bool = False, **microlink_options: Any) -> tuple[bool, str]:
        """
        Performs a GET request using the configured evasion and retry logic.

        Args:
            url: The destination URL.
            use_microlink: If True, uses the Microlink headless browser API.
            **microlink_options: Keyword arguments for Microlink parameters.

        Returns:
            A tuple of (success_boolean, response_text).
        """

        async def _attempt() -> tuple[bool, str]:
            await self.mimicry.apply_jitter()

            if use_microlink:
                return await self._fetch_with_microlink(url, **microlink_options)

            session = self._get_session()
            headers = {"Referer": "https://www.google.com/"}

            try:
                response = await session.get(url, headers=headers, timeout=self.config.http_timeout)
                await self._handle_response_status(response.status_code)
                return response.status_code == 200, response.text
            except (curl_requests.RequestsError, httpx.HTTPError) as exc:
                logger.error("Request failed: %s", exc)
                self._session = None
                raise

        try:
            return await self.retry.run(_attempt)
        except (curl_requests.RequestsError, httpx.HTTPError):
            logger.exception("Request failed after retries: %s", url)
            return False, ""

    async def _fetch_with_microlink(self, url: str, **microlink_options: Any) -> tuple[bool, str]:
        """
        Executes a request via the Microlink API.

        Note: Standard proxy settings may not propagate through Microlink
        unless supported by the specific API subscription.
        """
        async with httpx.AsyncClient(timeout=self.config.http_timeout) as client:
            response = await client.get(
                "https://api.microlink.io",
                params={"url": url, **microlink_options},
                follow_redirects=True,
            )
            data: dict[str, Any] = response.json()
            status_val = data.get("status")
            status: bool = False
            if isinstance(status_val, str) and status_val == "success":
                status = True
            result: str = str(data.get("data", {}))
            return status, result

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

    def close_session(self) -> None:
        """Explicitly closes the active session and clears state."""
        if self._session:
            self._session.close()
            self._session = None
