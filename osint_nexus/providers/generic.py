"""
Generic provider for any platform with a simple URL template.

Can be instantiated with a custom URL pattern for platforms that
do not need specialised parsing.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from osint_nexus.core.dork import DorkEngine
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.providers.generic")


class SiteConfig(BaseModel):
    """Schema for a generic site provider."""

    name: str
    url_template: str
    error_indicator: str | None = None
    regex_pattern: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    dork_query: str | None = None


class GenericProvider(BaseProvider):
    """
    A provider that checks username existence via a formatted URL.
    Validated via SiteConfig schema.
    """

    def __init__(
        self,
        config: SiteConfig,
        network: NetworkManager,
        dork_engine: DorkEngine | None = None,
    ) -> None:
        super().__init__(config.name, network)
        self.config = config
        self.dork_engine = dork_engine or DorkEngine()

    async def check_username(self, username: str, **kwargs: Any) -> tuple[bool, str]:
        """Fetch the profile page and return (found, content)."""
        url = self.config.url_template.format(username)
        # Use provided headers if any
        found, content = await self.network.fetch(url, headers=self.config.headers)

        # Simple detection logic based on configuration
        if self.config.error_indicator and self.config.error_indicator in content:
            return False, content

        if self.config.regex_pattern:
            import re

            if not re.search(self.config.regex_pattern, content):
                return False, content

        return found, content

    def get_dork_query(self, username: str) -> str:
        """Return a dork query for the platform."""
        if self.config.dork_query:
            return self.config.dork_query.format(username=username)
        return self.dork_engine.get_dork_query(username, self.name)
