from typing import Any

from osint_nexus.core.config import get_config
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager


class GitHubProvider(BaseProvider):
    """Provider for GitHub OSINT.

    Searches for user profiles on github.com.
    """

    def __init__(self, network: NetworkManager) -> None:
        """Initialize GitHub provider.

        Args:
            network: NetworkManager instance for making requests.
        """
        super().__init__("GitHub", network)
        self.url_template = get_config().service_urls["github"]

    async def check_username(self, username: str, **kwargs: Any) -> tuple[bool, str]:
        """Check if a username exists on GitHub.

        Args:
            username: The username to search for.
            **kwargs: Additional arguments.

        Returns:
            A tuple containing a boolean (exists or not) and a message.
        """
        url = self.url_template.format(username)
        # Use the injected network manager to handle evasion
        found, content = await self.network.fetch(url)
        return found, content

    def get_dork_query(self, username: str) -> str:
        """Generate a Google dork query for the given username.

        Args:
            username: The username to search for.

        Returns:
            A string containing the Google dork query.
        """
        return f"site:github.com {username}"

    def get_metadata(self, username: str) -> dict[str, Any]:
        """Get GitHub-specific metadata.

        Args:
            username: The username to search for.

        Returns:
            A dictionary containing provider-specific metadata.
        """
        # Metadata should ideally be fetched dynamically or configured properly
        return {"cpes": [], "ports": [443], "mac_address": None}
