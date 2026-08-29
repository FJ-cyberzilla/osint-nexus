"""
Abstract base class for all OSINT providers.

Defines the minimal interface that every platform‑specific check must
implement. The registry injects the shared NetworkManager so that
providers can make HTTP requests with evasion already built in.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from osint_nexus.core.provider_types import JSONValue, MetadataDict
    from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.providers.base")


@runtime_checkable
class ProviderProtocol(Protocol):
    """Protocol for provider interface."""

    name: str

    async def check_username(self, username: str, **kwargs: JSONValue) -> tuple[bool, str]: ...
    def get_dork_query(self, username: str) -> str: ...
    def get_metadata(self, username: str) -> MetadataDict: ...
    async def health_check(self) -> bool: ...


class BaseProvider(ABC):
    """
    Skeleton for username‑checking providers.

    Subclasses need only implement `check_username` and `get_dork_query`.
    They automatically have access to the project's NetworkManager for
    robust, evasive HTTP requests.
    """

    def __init__(self, name: str, network: NetworkManager) -> None:
        self.name = name
        self.network = network

    # ------------------------------------------------------------------
    # Provider interface
    # ------------------------------------------------------------------
    @abstractmethod
    async def check_username(self, username: str, **kwargs: JSONValue) -> tuple[bool, str]:
        """
        Determine if the username is registered on the platform.

        Args:
            username: The target username (raw, not sanitized).
            **kwargs: Additional arguments for provider flexibility.

        Returns:
            A tuple of (found, content). ``found`` indicates whether
            the username appears to exist; ``content`` is the raw
            response text for later validation.
        """
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def get_dork_query(self, username: str) -> str:
        """
        Generate a Google‑style dork query for manual verification.

        Args:
            username: The target username.

        Returns:
            A formatted search string.
        """
        raise NotImplementedError("Method not implemented")

    def get_metadata(self, username: str) -> MetadataDict:
        """
        Get provider-specific metadata.
        """
        return {}

    # ------------------------------------------------------------------
    # Optional lifecycle & utilities
    # ------------------------------------------------------------------
    async def health_check(self) -> bool:
        """
        Providers are considered healthy if their network backend is
        reachable. Override for custom checks (e.g., API key validity).
        """
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
