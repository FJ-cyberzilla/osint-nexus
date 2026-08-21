import asyncio
from typing import Protocol

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.exceptions import NetworkError
from osint_nexus.core.type_defs import JSONValue
from osint_nexus.utils.limiter import RateLimiter
from osint_nexus.utils.network_monitor import NetworkMonitor
from osint_nexus.utils.network_types import NETWORK_EXCEPTION, SessionProtocol
from osint_nexus.utils.session_manager import SessionManager


class BaseFetcher(Protocol):
    async def fetch(self, url: str, site_name: str | None, **kwargs: JSONValue) -> tuple[bool, str]: ...


class HttpFetcher:
    def __init__(
        self,
        config: Config,
        evasion: EvasionAgent,
        monitor: NetworkMonitor,
        session_manager: SessionManager,
        rate_limiter: RateLimiter,
    ) -> None:
        self.config = config
        self.evasion = evasion
        self.monitor = monitor
        self.session_manager = session_manager
        self.rate_limiter = rate_limiter

    def _prepare_headers(self, custom_headers: dict[str, str] | None) -> dict[str, str]:
        request_headers = {"Referer": "https://www.google.com/", "Accept-Language": "en-US,en;q=0.9"}
        if custom_headers:
            request_headers.update(custom_headers)
        if "User-Agent" not in request_headers and hasattr(self.config, "user_agents"):
            import random

            request_headers["User-Agent"] = random.choice(self.config.user_agents)  # nosec B311
        return request_headers

    async def _execute_http_request(
        self, session: SessionProtocol, url: str, headers: dict[str, str]
    ) -> tuple[int, str]:
        response = await session.get(url, headers=headers, timeout=self.monitor.dynamic_timeout)
        return response.status_code, response.text

    async def fetch(
        self, url: str, site_name: str | None, headers: dict[str, str] | None = None, **kwargs: JSONValue
    ) -> tuple[bool, str]:
        session = await self.session_manager.get_session()
        request_headers = self._prepare_headers(headers)

        start_time = asyncio.get_event_loop().time()
        try:
            status_code, text = await self._execute_http_request(session, url, request_headers)

            response_time = asyncio.get_event_loop().time() - start_time
            await self.rate_limiter.report(site_name, status_code, response_time)
            self.monitor.adapt(response_time)
            await self.monitor.handle_status(status_code)
            return status_code in (200, 201, 204), text
        except NETWORK_EXCEPTION as exc:
            await self.session_manager.close()
            raise NetworkError(f"HTTP failure: {exc}") from exc


class BrowserFetcher:
    def __init__(
        self,
        config: Config,
        monitor: NetworkMonitor,
        browser_pool: BrowserPoolManager,
        rate_limiter: RateLimiter,
    ) -> None:
        self.config = config
        self.monitor = monitor
        self.browser_pool = browser_pool
        self.rate_limiter = rate_limiter

    async def fetch(self, url: str, site_name: str | None, **kwargs: JSONValue) -> tuple[bool, str]:
        try:
            async with self.browser_pool.acquire_context() as context:
                page = await context.new_page()
                timeout_ms = int(self.monitor.dynamic_timeout * 1000)
                start_time = asyncio.get_event_loop().time()
                # Assuming `page.goto` can handle these keyword arguments
                response = await page.goto(url, timeout=timeout_ms, **kwargs)
                response_time = asyncio.get_event_loop().time() - start_time
                content = await page.content()
                if response:
                    # 'response' might not have a 'status' attribute as expected by the previous code.
                    # Wait, 'response' in Playwright is `Response` object which *does* have `status`.
                    # The type hint might be wrong.
                    await self.rate_limiter.report(site_name, response.status, response_time)
                    await self.monitor.handle_status(response.status)
                return (response is not None and response.status == 200), content
        except Exception as exc:
            raise NetworkError(f"Browser failure: {exc}") from exc
