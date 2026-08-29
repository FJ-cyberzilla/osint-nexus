from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


# JSON types that allow recursive structures
# Replaced recursive TypeAlias with a safer approach to avoid Pydantic RecursionError
@dataclass
class JSONDict:
    data: dict[str, JSONValue]


@dataclass
class JSONListContainer:
    data: list[JSONValue]


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
