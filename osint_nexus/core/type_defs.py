from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict, overload, Iterator
from collections.abc import Mapping, Sequence


# JSON types that allow recursive structures
# Replaced recursive TypeAlias with a safer approach to avoid Pydantic RecursionError
@dataclass
class JSONDict(Mapping[str, JSONValue]):
    data: dict[str, JSONValue]

    def __getitem__(self, key: str) -> JSONValue:
        return self.data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)


@dataclass
class JSONListContainer(Sequence[JSONValue]):
    data: list[JSONValue]

    @overload
    def __getitem__(self, index: int) -> JSONValue: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[JSONValue]: ...

    def __getitem__(self, index: int | slice) -> JSONValue | Sequence[JSONValue]:
        if isinstance(index, slice):
            return JSONListContainer(data=self.data[index])
        return self.data[index]

    def __len__(self) -> int:
        return len(self.data)


type JSONValue = str | int | float | bool | None | JSONDict | JSONListContainer
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
        return JSONDict(data={str(k): to_json_value(v) for k, v in value.items()})
    if isinstance(value, list):
        return JSONListContainer(data=[to_json_value(v) for v in value])
    return str(value)
