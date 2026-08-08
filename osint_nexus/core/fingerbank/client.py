from __future__ import annotations

import logging
from typing import Any

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
        session: Any,
        url: str,
        headers: dict[str, str],
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if method == "POST":
            return await session.post(
                url, json=payload, headers=headers, timeout=self.monitor.dynamic_timeout
            )
        return await session.get(url, headers=headers, timeout=self.monitor.dynamic_timeout)


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
        self.devices = DevicesClient(self)
        self.oui = OuiClient(self)
        self.static = StaticDataClient(self)
        self.users = UsersClient(self)

    def _handle_response(self, response: Any) -> Any:
        if response.status_code == 401:
            raise FingerbankUnauthorizedError("Invalid API key.")
        if response.status_code == 403:
            raise FingerbankForbiddenError("Account blocked.")
        if response.status_code == 429:
            raise FingerbankRateLimitedError("Rate limit exceeded.")
        if response.status_code == 502:
            raise FingerbankBackendError("Backend error.")
        if response.status_code == 404:
            raise FingerbankNotFoundError("No device result found.")

        if response.status_code != 200:
            raise Exception(f"Unexpected error: {response.status_code}")

        return response

    async def _get(self, endpoint: str) -> Any:
        if not self.is_enabled:
            return None
        url = f"{self.BASE_URL}{endpoint}?key={self.api_key}"
        session = await self.network.session_manager.get_session()
        response = await self.fetcher._execute_http_request(session, url, {})
        return self._handle_response(response)

    async def interrogate(self, payload: dict[str, Any]) -> InterrogateResponse | None:
        if not self.is_enabled:
            logger.info("Fingerbank is disabled (Missing API Key).")
            return None

        url = f"{self.BASE_URL}combinations/interrogate?key={self.api_key}"
        headers = {"Content-type": "application/json"}

        session = await self.network.session_manager.get_session()
        response = await self.fetcher._execute_http_request(
            session, url, headers, method="POST", payload=payload
        )

        response = self._handle_response(response)
        return InterrogateResponse.from_dict(response.json())
