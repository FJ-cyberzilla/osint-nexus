from typing import Any

from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager


class AparatProvider(BaseProvider):
    def __init__(self, network: NetworkManager):
        super().__init__("Aparat", network)
        self.url_template = "https://www.aparat.com/{}"

    async def check_username(self, username: str, **kwargs: Any) -> tuple[bool, str]:
        url = self.url_template.format(username)
        return await self.network.fetch(url)

    def get_dork_query(self, username: str) -> str:
        return f"site:aparat.com {username}"
