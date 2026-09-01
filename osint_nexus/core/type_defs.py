from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict, overload

from pydantic import RootModel

# JSON types that allow recursive structures
# Replaced recursive TypeAlias with a safer approach to avoid Pydantic RecursionError
type JSONValue = str | int | float | bool | None | JSONDict | JSONListContainer


class JSONDict(RootModel[dict[str, JSONValue]]):
    root: dict[str, JSONValue]

    def __getitem__(self, key: str) -> JSONValue:
        return self.root[key]

    def __len__(self) -> int:
        return len(self.root)

    def get(self, key: str, default: JSONValue = None) -> JSONValue:
        return self.root.get(key, default)


class JSONListContainer(RootModel[list[JSONValue]]):
    root: list[JSONValue]

    @overload
    def __getitem__(self, index: int) -> JSONValue: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[JSONValue]: ...

    def __getitem__(self, index: int | slice) -> JSONValue | Sequence[JSONValue]:
        if isinstance(index, slice):
            return JSONListContainer(root=self.root[index])
        return self.root[index]

    def __len__(self) -> int:
        return len(self.root)


type JSONObject = dict[str, JSONValue]
type JSONList = list[JSONValue]

# Telemetry types
type TelemetryValue = str | float | int | bool
type TelemetryDict = dict[str, TelemetryValue]

# Metadata dictionary for general usage
type MetadataDict = dict[str, JSONValue]


class IOCType(Enum):
    IPV4 = "ipv4"
    DOMAIN = "domain"
    SHA256 = "sha256"
    MD5 = "md5"
    EMAIL = "email"


@dataclass(frozen=True)
class ExtractedIOC:
    type: IOCType
    value: str


class SocialHandle(TypedDict):
    platform: str
    username: str
    url: str


class PlatformIdentity(TypedDict):
    platform: str
    username: str


class LinkHarvestResult(TypedDict):
    external_links: list[str]
    social_handles: list[SocialHandle]


class ExtractedPivots(TypedDict):
    emails: list[str]
    pgp_keys: list[str]
    external_links: list[str]
    social_handles: list[SocialHandle]
    bio: str | None


class IntelligenceMetadata(TypedDict, total=False):
    fingerprint_results: dict[str, JSONValue]
    device_inference: dict[str, JSONValue]
    emails: list[str]
    pgp_keys: list[str]
    external_links: list[str]
    social_handles: list[SocialHandle]
    bio: str | None
    error: str


def ensure_type[T](value: JSONValue, expected_type: type[T] | tuple[type[T], ...]) -> T | None:
    """Safely cast a JSONValue to an expected type if it matches."""
    if isinstance(value, expected_type):
        return value
    return None


def to_json_value(value: object) -> JSONValue:
    """Convert an object to a JSONValue."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return JSONDict(root={str(k): to_json_value(v) for k, v in value.items()})
    if isinstance(value, list):
        return JSONListContainer(root=[to_json_value(v) for v in value])
    return str(value)
