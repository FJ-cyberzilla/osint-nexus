from collections.abc import Mapping
from typing import TypedDict

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue

HttpData = Mapping[str, JSONValue]


class HttpResultData(TypedDict):
    platform: JSONValue
    mobile: JSONValue
    architecture: JSONValue
    language: JSONValue
    full_headers: Mapping[str, JSONValue]


class HttpResult(TypedDict):
    name: str
    data: HttpResultData
    confidence: float


class HttpFingerprintStrategy(FingerprintStrategy[HttpData, Mapping[str, JSONValue]]):
    """Strategy for parsing HTTP headers for device info."""

    name: str = "http_headers"

    @beartype
    def extract(self, data: HttpData) -> Mapping[str, JSONValue]:
        # More precise: ensure all header values are strings
        headers: dict[str, str] = {k: str(v) for k, v in data.items()}

        # Deep extraction of all Sec-CH-UA headers
        sec_ch_ua_headers = {k: v for k, v in data.items() if k.lower().startswith("sec-ch-ua")}

        fingerprint: HttpResultData = {
            "platform": headers.get("sec-ch-ua-platform"),
            "mobile": headers.get("sec-ch-ua-mobile") == "?1",
            "architecture": headers.get("sec-ch-ua-arch"),
            "language": headers.get("accept-language"),
            "full_headers": sec_ch_ua_headers,
        }

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": 0.85,
        }
