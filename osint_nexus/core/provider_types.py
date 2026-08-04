from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderExecutionResult:
    """Standardized result object for provider execution."""

    found: bool
    content: str
    error: Exception | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None


class ValidatorProtocol(Protocol):
    """Interface for provider result validation."""

    def validate(self, content: str, provider_name: str) -> bool: ...


class DatabaseManagerProtocol(Protocol):
    """Interface for result persistence."""

    async def save_result(self, username: str, provider: str, found: bool) -> None: ...


# Common dictionary type for metadata and options
type JSONValue = str | int | float | bool | None | dict[str, "JSONValue"] | list["JSONValue"]
type MetadataDict = dict[str, JSONValue]


class DeviceInferenceProtocol(Protocol):
    """Interface for device inference."""

    async def infer(self, content: str, metadata: MetadataDict) -> Any: ...
