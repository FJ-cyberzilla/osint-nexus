from __future__ import annotations

import logging
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from osint_nexus.utils.network_types import ResponseProtocol, SessionProtocol
    from osint_nexus.core.fingerbank.clients.devices import DevicesClient
    from osint_nexus.core.fingerbank.clients.oui import OuiClient
    from osint_nexus.core.fingerbank.clients.static import StaticDataClient
    from osint_nexus.core.fingerbank.clients.users import UsersClient

from osint_nexus.core.fingerbank.exceptions import (
    FingerbankBackendError,
    FingerbankForbiddenError,
    FingerbankNotFoundError,
    FingerbankRateLimitedError,
    FingerbankUnauthorizedError,
)
from osint_nexus.core.fingerbank.models import InterrogateResponse
from osint_nexus.utils.fetchers import HttpFetcher
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.core.fingerbank.client")


class FingerbankHttpFetcher(HttpFetcher):
    async def _execute_http_request(
        self,
        session: SessionProtocol,
        url: str,
        headers: dict[str, str],
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> tuple[int, str]:
        if method == "POST":
            resp = await session.post(
                url, json=payload, headers=headers, timeout=self.monitor.dynamic_timeout
            )
        else:
            resp = await session.get(url, headers=headers, timeout=self.monitor.dynamic_timeout)
        return resp.status_code, resp.text


class FingerbankClient:
    BASE_URL = "https://api.fingerbank.org/api/v2/"

    def __init__(self, network: NetworkManager, api_key: str | None = None) -> None:
        self.network = network
        self.api_key = api_key
        self.is_enabled = bool(api_key)
        self.fetcher = FingerbankHttpFetcher(
            network.config, network.evasion, network.monitor, network.session_manager, network.rate_limiter
        )
        # Facade components
        from osint_nexus.core.fingerbank.clients.devices import DevicesClient
        from osint_nexus.core.fingerbank.clients.oui import OuiClient
        from osint_nexus.core.fingerbank.clients.static import StaticDataClient
        from osint_nexus.core.fingerbank.clients.users import UsersClient

        self.devices = DevicesClient(self)
        self.oui = OuiClient(self)
        self.static = StaticDataClient(self)
        self.users = UsersClient(self)

    def _handle_response(self, status_code: int, text: str) -> tuple[int, str]:
        if status_code == 401:
            raise FingerbankUnauthorizedError("Invalid API key.")
        if status_code == 403:
            raise FingerbankForbiddenError("Account blocked.")
        if status_code == 429:
            raise FingerbankRateLimitedError("Rate limit exceeded.")
        if status_code == 502:
            raise FingerbankBackendError("Backend error.")
        if status_code == 404:
            raise FingerbankNotFoundError("No device result found.")

        if status_code != 200:
            raise Exception(f"Unexpected error: {status_code}")

        return status_code, text

    async def _get(self, endpoint: str) -> tuple[int, str] | None:
        if not self.is_enabled:
            return None
        url = f"{self.BASE_URL}{endpoint}?key={self.api_key}"
        session = await self.network.session_manager.get_session()
        status_code, text = await self.fetcher._execute_http_request(session, url, {})
        return self._handle_response(status_code, text)

    async def interrogate(self, payload: dict[str, Any]) -> InterrogateResponse | None:
        if not self.is_enabled:
            logger.info("Fingerbank is disabled (Missing API Key).")
            return None

        url = f"{self.BASE_URL}combinations/interrogate?key={self.api_key}"
        headers = {"Content-type": "application/json"}

        session = await self.network.session_manager.get_session()
        status_code, text = await self.fetcher._execute_http_request(
            session, url, headers, method="POST", payload=payload
        )

        status_code, text = self._handle_response(status_code, text)
        return InterrogateResponse.model_validate(json.loads(text))
