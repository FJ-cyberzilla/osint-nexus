import httpx
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager
from typing import Tuple, Any


class GitHubProvider(BaseProvider):
    def __init__(self, network: NetworkManager):
        super().__init__("GitHub", network)
        self.url_template = "https://github.com/{}"

    async def check_username(self, username: str, **kwargs: Any) -> Tuple[bool, str]:
        url = self.url_template.format(username)
        # Use the injected network manager to handle evasion
        found, content = await self.network.fetch(url)
        return found, content

    def get_dork_query(self, username: str) -> str:
        return f"site:github.com {username}"

    def get_metadata(self, username: str) -> dict[str, Any]:
        return {
            "cpes": ["cpe:/o:linux:kernel:5.15"],
            "ports": [22],
            "mac_address": "B8:27:EB:12:34:56"
        }
