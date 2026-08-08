from typing import Any, TypedDict

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy

HttpData = dict[str, Any]


class HttpResultData(TypedDict):
    platform: str | None
    mobile: bool
    architecture: str | None
    language: str | None
    full_headers: dict[str, str]


class HttpResult(TypedDict):
    name: str
    data: HttpResultData
    confidence: float


class HttpFingerprintStrategy(FingerprintStrategy[HttpData, HttpResult]):
    """Strategy for parsing HTTP headers for device info."""

    name: str = "http_headers"

    @beartype
    def extract(self, data: HttpData) -> HttpResult:
        # More precise: ensure all header values are strings
        headers: dict[str, str] = {k: str(v) for k, v in data.items()}

        # Deep extraction of all Sec-CH-UA headers
        sec_ch_ua_headers = {k: v for k, v in headers.items() if k.lower().startswith("sec-ch-ua")}

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
