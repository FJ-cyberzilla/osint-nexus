from __future__ import annotations

from typing import cast, TypedDict, TypeAlias
from enum import Enum
from dataclasses import dataclass

# JSON types that allow recursive structures
JSONValue: TypeAlias = (
    str | int | float | bool | None | dict[str, "JSONValue"] | list["JSONValue"]
)
JSONObject: TypeAlias = dict[str, JSONValue]
JSONList: TypeAlias = list[JSONValue]

# Telemetry types
TelemetryValue: TypeAlias = str | float | int | bool
TelemetryDict: TypeAlias = dict[str, TelemetryValue]

# Metadata dictionary for general usage
MetadataDict: TypeAlias = dict[str, JSONValue]

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


def ensure_type[T](value: JSONValue, expected_type: type[T] | tuple[type[T], ...]) -> T | None:
    """Safely cast a JSONValue to an expected type if it matches."""
    if isinstance(value, expected_type):
        return value
    return None
