from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from osint_nexus.core.types import JSONValue, MetadataDict


@dataclass(frozen=True)
class ProviderExecutionResult:
    """Standardized result object for provider execution."""

    found: bool
    content: str
    error: Exception | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Interface for provider result validation."""

    def validate(self, content: str, provider_name: str) -> bool:
        pass


@runtime_checkable
class DatabaseManagerProtocol(Protocol):
    """Interface for result persistence."""

    async def save_result(self, username: str, provider: str, found: bool) -> None: ...


__all__ = [
    "ProviderExecutionResult",
    "ValidatorProtocol",
    "DatabaseManagerProtocol",
    "JSONValue",
    "MetadataDict",
    "DeviceInferenceProtocol",
]


@runtime_checkable
class DeviceInferenceProtocol(Protocol):
    """Interface for device inference."""

    async def infer(self, content: str, metadata: MetadataDict) -> object: ...
