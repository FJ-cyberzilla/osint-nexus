import asyncio
import contextlib
import random
from typing import Any, cast

from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.utils.network_types import HAS_CURL_CFFI, ResponseProtocol, SessionProtocol

with contextlib.suppress(ImportError):
    import curl_cffi.requests as curl_requests


class SessionWrapper:
    def __init__(self, session: Any) -> None:
        self._session = session

    async def aclose(self) -> None:
        if hasattr(self._session, "aclose"):
            await self._session.aclose()
        else:
            await self._session.close()

    async def close(self) -> None:
        if hasattr(self._session, "aclose"):
            await self._session.aclose()
        else:
            await self._session.close()

    async def get(self, url: str, **kwargs: Any) -> ResponseProtocol:
        return cast(ResponseProtocol, await self._session.get(url, **kwargs))

    async def post(self, url: str, **kwargs: Any) -> ResponseProtocol:
        return cast(ResponseProtocol, await self._session.post(url, **kwargs))


class SessionManager:
    """Manages HTTP sessions and proxy rotation."""

    def __init__(self, config: Config, evasion: EvasionAgent, dynamic_timeout: float) -> None:
        self.config = config
        self.evasion = evasion
        self.dynamic_timeout = dynamic_timeout
        self._session: SessionProtocol | None = None
        self._current_proxy: str | None = None
        self._current_profile: str | None = None
        self._session_lock = asyncio.Lock()

    def _init_curl_session(self, new_proxy: str | None) -> SessionProtocol:
        profiles = getattr(self.config, "TLS_PROFILES", ["chrome120", "edge114", "safari15_3"])
        self._current_profile = str(random.choice(profiles))  # nosec B311
        return SessionWrapper(
            curl_requests.AsyncSession(
                impersonate=self._current_profile,
                proxy=new_proxy,
                timeout=self.dynamic_timeout,
            )
        )

    def _init_httpx_session(self, new_proxy: str | None) -> SessionProtocol:
        import httpx

        client = httpx.AsyncClient(proxy=new_proxy, timeout=self.dynamic_timeout, follow_redirects=True)
        return SessionWrapper(client)

    async def _handle_existing_session(self) -> None:
        if self._session is not None:
            if HAS_CURL_CFFI:
                await self._session.close()
            else:
                await self._session.aclose()

    async def _create_new_session(self, new_proxy: str | None) -> None:
        self._current_proxy = new_proxy
        if HAS_CURL_CFFI:
            self._session = self._init_curl_session(new_proxy)
        else:
            self._session = self._init_httpx_session(new_proxy)

    async def get_session(self) -> SessionProtocol:
        new_proxy = self.evasion.get_proxy()
        async with self._session_lock:
            if self._session is None or new_proxy != self._current_proxy:
                await self._handle_existing_session()
                await self._create_new_session(new_proxy)
            return self._session  # type: ignore[return-value]

    async def close(self) -> None:
        async with self._session_lock:
            if self._session:
                if HAS_CURL_CFFI:
                    await self._session.close()
                else:
                    await self._session.aclose()
                self._session = None
