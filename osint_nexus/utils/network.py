import asyncio
import logging
import random
from types import TracebackType
from typing import Any, Self, cast

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


class SessionManager:
    """Manages curl_cffi sessions and proxy rotation."""

    def __init__(self, config: Config, evasion: EvasionAgent, dynamic_timeout: float) -> None:
        self.config = config
        self.evasion = evasion
        self.dynamic_timeout = dynamic_timeout
        self._session: curl_requests.AsyncSession | None = None
        self._current_proxy: str | None = None
        self._current_profile: str | None = None
        self._session_lock = asyncio.Lock()

    async def get_session(self) -> curl_requests.AsyncSession:
        new_proxy = self.evasion.get_proxy()
        async with self._session_lock:
            if self._session is None or new_proxy != self._current_proxy:
                if self._session is not None:
                    await self._session.close()
                profiles = getattr(self.config, "TLS_PROFILES", ["chrome120", "edge114", "safari15_3"])
                self._current_profile = random.choice(profiles)  # nosec B311
                self._current_proxy = new_proxy
                self._session = curl_requests.AsyncSession(
                    impersonate=cast(Any, self._current_profile),
                    proxy=self._current_proxy,
                    timeout=self.dynamic_timeout,
                )
            return self._session

    async def close(self) -> None:
        async with self._session_lock:
            if self._session:
                await self._session.close()
                self._session = None


class NetworkMonitor:
    """Monitors environment and manages response status."""

    def __init__(self, config: Config, evasion: EvasionAgent) -> None:
        self.config = config
        self.evasion = evasion
        self.dynamic_timeout: float = float(config.http_timeout)

    def adapt(self, response_time: float) -> None:
        if response_time > (self.dynamic_timeout * 0.8):
            new_timeout = min(self.dynamic_timeout * 1.5, float(self.config.http_timeout * 2.5))
            if new_timeout != self.dynamic_timeout:
                self.dynamic_timeout = new_timeout

    async def handle_status(self, status_code: int) -> None:
        if status_code in (403, 429, 401, 407):
            await self.evasion.report_failure(status_code)
            self.dynamic_timeout = min(self.dynamic_timeout * 1.2, float(self.config.http_timeout * 3))


class NetworkManager:
    """
    Manages HTTP request lifecycles with evasion, retry, and persistent TLS sessions.
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
        self.monitor = NetworkMonitor(config, evasion)
        self.session_manager = SessionManager(config, evasion, self.monitor.dynamic_timeout)

    async def fetch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        use_browser: bool = False,
        **browser_options: Any,
    ) -> tuple[bool, str]:
        async def _attempt() -> tuple[bool, str]:
            await self.mimicry.apply_jitter()
            if use_browser:
                return await self._fetch_with_browser(url, **browser_options)
            return await self._fetch_with_curl(url, headers)

        try:
            return await self.retry.run(_attempt)
        except Exception as exc:
            logger.error("Request totally failed for %s: %s", url, exc)
            await self.session_manager.close()
            return False, ""

    async def _fetch_with_curl(self, url: str, custom_headers: dict[str, str] | None) -> tuple[bool, str]:
        session = await self.session_manager.get_session()
        request_headers = {"Referer": "https://www.google.com/", "Accept-Language": "en-US,en;q=0.9"}
        if custom_headers:
            request_headers.update(custom_headers)
        if "User-Agent" not in request_headers and hasattr(self.config, "user_agents"):
            request_headers["User-Agent"] = random.choice(self.config.user_agents)  # nosec B311

        start_time = asyncio.get_event_loop().time()
        try:
            response = await session.get(url, headers=request_headers, timeout=self.monitor.dynamic_timeout)
            self.monitor.adapt(asyncio.get_event_loop().time() - start_time)
            await self.monitor.handle_status(response.status_code)
            return response.status_code in (200, 201, 204), str(response.text)
        except curl_requests.RequestsError as exc:
            await self.session_manager.close()
            raise NetworkManagerError(f"cURL failure: {exc}") from exc

    async def _fetch_with_browser(self, url: str, **browser_options: Any) -> tuple[bool, str]:
        try:
            async with self.browser_pool.acquire_context() as context:
                page = await context.new_page()
                timeout_ms = int(self.monitor.dynamic_timeout * 1000)
                response = await page.goto(url, timeout=timeout_ms, **browser_options)
                content = await page.content()
                if response:
                    await self.monitor.handle_status(response.status)
                return (response is not None and response.status == 200), content
        except Exception as exc:
            raise NetworkManagerError(f"Browser failure: {exc}") from exc

    async def close_all(self) -> None:
        await self.session_manager.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close_all()
