import logging
from types import TracebackType
from typing import Any, Self

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.exceptions import NetworkError
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.utils.fetchers import BrowserFetcher, HttpFetcher
from osint_nexus.utils.limiter import AdaptiveRateLimiter, RateLimiter
from osint_nexus.utils.network_monitor import NetworkMonitor
from osint_nexus.utils.retry import RetryHandler
from osint_nexus.utils.session_manager import SessionManager

logger = logging.getLogger("osint_nexus.network")


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
        self.retry = RetryHandler(config)
        self.monitor = NetworkMonitor(config, evasion)
        self.session_manager = SessionManager(config, evasion, self.monitor.dynamic_timeout)
        self.rate_limiter = rate_limiter or AdaptiveRateLimiter()

        self.http_fetcher = HttpFetcher(
            config, evasion, self.monitor, self.session_manager, self.rate_limiter
        )
        self.browser_fetcher = BrowserFetcher(config, self.monitor, browser_pool, self.rate_limiter)

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
                return await self.browser_fetcher.fetch(url, site_name, **browser_options)
            return await self.http_fetcher.fetch(url, site_name, headers=headers)

        try:
            return await self.retry.run(_attempt)
        except NetworkError as exc:
            logger.error("Request totally failed for %s: %s", url, exc)
            await self.session_manager.close()
            return False, ""

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
