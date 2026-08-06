import asyncio
import logging
import random
from types import TracebackType
from typing import Any, Self

try:
    import curl_cffi.requests as curl_requests

    HAS_CURL_CFFI = True
    NETWORK_EXCEPTION = curl_requests.RequestsError
except ImportError:
    import httpx

    HAS_CURL_CFFI = False
    NETWORK_EXCEPTION = httpx.HTTPError

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.exceptions import NetworkError
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.utils.limiter import AdaptiveRateLimiter, RateLimiter
from osint_nexus.utils.retry import RetryHandler

logger = logging.getLogger("osint_nexus.network")


class SessionManager:
    """Manages HTTP sessions and proxy rotation."""

    def __init__(self, config: Config, evasion: EvasionAgent, dynamic_timeout: float) -> None:
        self.config = config
        self.evasion = evasion
        self.dynamic_timeout = dynamic_timeout
        self._session: Any | None = None
        self._current_proxy: str | None = None
        self._current_profile: str | None = None
        self._session_lock = asyncio.Lock()

    async def get_session(self) -> Any:
        new_proxy = self.evasion.get_proxy()
        async with self._session_lock:
            if self._session is None or new_proxy != self._current_proxy:
                if self._session is not None:
                    await self._session.aclose() if not HAS_CURL_CFFI else await self._session.close()

                self._current_proxy = new_proxy

                if HAS_CURL_CFFI:
                    profiles = getattr(self.config, "TLS_PROFILES", ["chrome120", "edge114", "safari15_3"])
                    self._current_profile = random.choice(profiles)  # nosec B311
                    self._session = curl_requests.AsyncSession(
                        impersonate=str(self._current_profile),
                        proxy=self._current_proxy,
                        timeout=self.dynamic_timeout,
                    )
                else:
                    proxies = (
                        {"http://": self._current_proxy, "https://": self._current_proxy}
                        if self._current_proxy
                        else None
                    )
                    self._session = httpx.AsyncClient(
                        proxies=proxies, timeout=self.dynamic_timeout, follow_redirects=True
                    )
            return self._session

    async def close(self) -> None:
        async with self._session_lock:
            if self._session:
                await self._session.aclose() if not HAS_CURL_CFFI else await self._session.close()
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
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.config = config
        self.evasion = evasion
        self.mimicry = mimicry
        self.browser_pool = browser_pool
        self.retry = RetryHandler(config)
        self.monitor = NetworkMonitor(config, evasion)
        self.session_manager = SessionManager(config, evasion, self.monitor.dynamic_timeout)
        self.rate_limiter = rate_limiter or AdaptiveRateLimiter()

    async def fetch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        use_browser: bool = False,
        site_name: str | None = None,
        **browser_options: Any,
    ) -> tuple[bool, str]:
        async def _attempt() -> tuple[bool, str]:
            await self.rate_limiter.wait(site_name)
            await self.mimicry.apply_jitter()
            if use_browser:
                return await self._fetch_with_browser(url, site_name, **browser_options)
            return await self._fetch_http(url, headers, site_name)

        try:
            return await self.retry.run(_attempt)
        except NetworkError as exc:
            logger.error("Request totally failed for %s: %s", url, exc)
            await self.session_manager.close()
            return False, ""

    async def _fetch_http(
        self, url: str, custom_headers: dict[str, str] | None, site_name: str | None
    ) -> tuple[bool, str]:
        session = await self.session_manager.get_session()
        request_headers = {"Referer": "https://www.google.com/", "Accept-Language": "en-US,en;q=0.9"}
        if custom_headers:
            request_headers.update(custom_headers)
        if "User-Agent" not in request_headers and hasattr(self.config, "user_agents"):
            request_headers["User-Agent"] = random.choice(self.config.user_agents)  # nosec B311

        start_time = asyncio.get_event_loop().time()
        try:
            if HAS_CURL_CFFI:
                response = await session.get(
                    url, headers=request_headers, timeout=self.monitor.dynamic_timeout
                )
            else:
                response = await session.get(
                    url, headers=request_headers, timeout=self.monitor.dynamic_timeout
                )

            response_time = asyncio.get_event_loop().time() - start_time
            await self.rate_limiter.report(site_name, response.status_code, response_time)
            self.monitor.adapt(response_time)
            await self.monitor.handle_status(response.status_code)
            return response.status_code in (200, 201, 204), str(response.text)
        except NETWORK_EXCEPTION as exc:
            await self.session_manager.close()
            raise NetworkError(f"HTTP failure: {exc}") from exc

    async def _fetch_with_browser(
        self, url: str, site_name: str | None, **browser_options: Any
    ) -> tuple[bool, str]:
        try:
            async with self.browser_pool.acquire_context() as context:
                page = await context.new_page()
                timeout_ms = int(self.monitor.dynamic_timeout * 1000)
                start_time = asyncio.get_event_loop().time()
                response = await page.goto(url, timeout=timeout_ms, **browser_options)
                response_time = asyncio.get_event_loop().time() - start_time
                content = await page.content()
                if response:
                    await self.rate_limiter.report(site_name, response.status, response_time)
                    await self.monitor.handle_status(response.status)
                return (response is not None and response.status == 200), content
        except Exception as exc:
            raise NetworkError(f"Browser failure: {exc}") from exc

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
