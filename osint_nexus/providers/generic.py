"""
Generic provider for any platform with a simple URL template.

Can be instantiated with a custom URL pattern for platforms that
do not need specialised parsing. Designed for high concurrency and
safe execution within the OSINT orchestration pipeline.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from pydantic import BaseModel, Field, field_validator

from osint_nexus.core.exceptions import NetworkError
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager

if TYPE_CHECKING:
    from osint_nexus.core.dork import DorkEngine
    from osint_nexus.core.provider_types import JSONValue
else:
    JSONValue = Any
    from typing import Any


class SiteConfig(BaseModel):
    """
    Schema for a generic site provider configuration.
    Immutable to ensure thread/async safety across the application lifecycle.
    """

    model_config = {"frozen": True}

    name: str = Field(..., description="The canonical name of the platform.")
    url_template: str = Field(..., description="URL template. Must contain the '{username}' placeholder.")
    error_indicator: str | None = Field(
        default=None, description="A substring that, if found, indicates the user does NOT exist."
    )
    regex_pattern: re.Pattern[str] | None = Field(
        default=None, description="A compiled regex pattern indicating user presence."
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="Custom HTTP headers to bypass basic blocks."
    )
    dork_query: str | None = Field(default=None, description="Custom Dork template containing '{username}'.")
    use_browser: bool = Field(default=False, description="Whether to route through a headless browser pool.")
    timeout: float = Field(default=15.0, description="Network timeout in seconds.")

    @field_validator("url_template")
    @classmethod
    def validate_url_template(cls, v: str) -> str:
        """Ensure the URL template is valid and contains the required formatting key."""
        if "{username}" not in v:
            raise ValueError(f"url_template '{v}' must contain the '{{username}}' placeholder.")
        return v

    @field_validator("regex_pattern", mode="before")
    @classmethod
    def compile_regex(cls, v: str | re.Pattern[str] | None) -> re.Pattern[str] | None:
        """Pre-compile regex for performance during high-volume async scans."""
        if isinstance(v, str):
            try:
                return re.compile(v, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{v}': {e}") from e
        return v


class GenericProvider(BaseProvider):
    """
    A generic OSINT provider that verifies username existence via HTTP requests.
    Validates existence using HTTP status, explicit error strings, or regex matching.
    """

    def __init__(
        self,
        config: SiteConfig,
        network: NetworkManager,
        dork_engine: DorkEngine | None = None,
    ) -> None:
        from osint_nexus.core.dork import DorkEngine as LazyDorkEngine

        super().__init__(config.name, network)
        self.config = config
        self.dork_engine = dork_engine or LazyDorkEngine()

        # Instance-specific logger for better observability in async traces
        self._logger = logging.getLogger(f"osint_nexus.providers.generic.{self.config.name}")

    async def check_username(self, username: str, **kwargs: JSONValue) -> tuple[bool, str]:
        """
        Fetch the profile page and return existence and content.

        Args:
            username: The target username to check.
            **kwargs: Additional arguments passed to the network fetcher.

        Returns:
            A tuple (found, content_string).
        """
        safe_username = quote(username)
        url = self.config.url_template.format(username=safe_username)

        self._logger.debug("Executing check for target URL: %s", url)

        found, content, error = await self._fetch(url, **kwargs)
        if error:
            return False, error

        # Ensure content is stringified safely for substring/regex matching
        content_str = str(content) if content else ""
        return self._detect(found, content_str)

    async def _fetch(self, url: str, **kwargs: JSONValue) -> tuple[bool, str | None, str | None]:
        """
        Fetch content from the network with retry and evasion.

        Args:
            url: The URL to fetch.
            **kwargs: Extra arguments for the request.

        Returns:
            A tuple (found, content_or_none, error_message_or_none).
        """
        try:
            found, content = await self.network.fetch(
                url,
                headers=self.config.headers,
                use_browser=self.config.use_browser,
                timeout=self.config.timeout,
                **kwargs,
            )
            return found, content, None
        except Exception as e:
            self._logger.error("Network constraint or exception occurred: %s", e, exc_info=True)
            return False, None, f"{NetworkError.__name__}: {str(e)}"

    def _detect(self, found: bool, content_str: str) -> tuple[bool, str]:
        """
        Detect username existence based on rules: error strings, regex, or fallback.

        Args:
            found: The boolean found status returned by the NetworkManager.
            content_str: The raw response content as a string.

        Returns:
            A tuple (detected_existence, content_string).
        """
        # 1. Negative Detection: Check for explicit error strings (e.g., "Page not found")
        if self.config.error_indicator and self.config.error_indicator in content_str:
            self._logger.debug("Match: Negative error indicator '%s' found.", self.config.error_indicator)
            return False, content_str

        # 2. Positive Detection: Check for specific regex profile indicators
        if self.config.regex_pattern:
            if not self.config.regex_pattern.search(content_str):
                self._logger.debug("Miss: Regex pattern failed to match.")
                return False, content_str
            # If regex matches, we confidently override network-level 'found' status
            return True, content_str

        # 3. Fallback: Rely on the NetworkManager's heuristic (usually HTTP 200 vs 404)
        self._logger.debug(
            "Detection inconclusive based on rules, falling back to HTTP heuristic: found=%s", found
        )
        return found, content_str

    def get_dork_query(self, username: str) -> str:
        """
        Return a search engine dork query for the platform.

        Args:
            username: The target username.

        Returns:
            A formatted dork query string.
        """
        if self.config.dork_query:
            try:
                return self.config.dork_query.format(username=username)
            except KeyError as e:
                self._logger.warning("Malformed dork_query template. Missing expected placeholder: %s", e)
                return self.config.dork_query

        # Fallback to the centralized DorkEngine if no custom query is defined
        return self.dork_engine.get_dork_query(username, self.name)
