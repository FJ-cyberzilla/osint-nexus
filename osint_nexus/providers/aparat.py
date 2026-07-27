from typing import Any

from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager


class AparatProvider(BaseProvider):
    """Provider for Aparat (Iranian video platform) OSINT.

    Searches for user profiles on aparat.com.
    """

    def __init__(self, network: NetworkManager):
        """Initialize Aparat provider.

        Args:
            network: NetworkManager instance for making requests.
        """
        super().__init__("Aparat", network)
        self.url_template = "https://www.aparat.com/{}"

    async def check_username(self, username: str, **kwargs: Any) -> tuple[bool, str]:
        """Check if a username exists on Aparat.

        Args:
            username: The username to search for.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing a boolean (exists or not) and a message.
        """
        url = self.url_template.format(username)
        return await self.network.fetch(url)

    def get_dork_query(self, username: str) -> str:
        """Generate a Google dork query for the given username.

        Args:
            username: The username to search for.

        Returns:
            A string containing the Google dork query.
        """
        return f"site:aparat.com {username}"
