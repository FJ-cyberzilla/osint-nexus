"""
Generic provider for any platform with a simple URL template.

Can be instantiated with a custom URL pattern for platforms that
do not need specialised parsing.
"""

from __future__ import annotations

from typing import Any

from osint_nexus.core.dork import DorkEngine
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager


class GenericProvider(BaseProvider):
    """
    A provider that checks username existence via a formatted URL.

    Example:
        provider = GenericProvider(
            name="example",
            url_template="https://example.com/user/{username}",
            network=network_manager,
        )
    """

    def __init__(self, name: str, url_template: str, network: NetworkManager) -> None:
        super().__init__(name, network)
        self.url_template = url_template

    async def check_username(self, username: str, **kwargs: Any) -> tuple[bool, str]:
        """Fetch the profile page and return (found, content)."""
        url = self.url_template.format(username)
        return await self.network.fetch(url)

    def get_dork_query(self, username: str) -> str:
        """Return a dork query for the platform."""
        return DorkEngine.get_dork_query_static(username, self.name)
