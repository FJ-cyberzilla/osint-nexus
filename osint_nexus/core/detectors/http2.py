from typing import NotRequired, TypedDict

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy


class Http2Data(TypedDict):
    alpn: NotRequired[str]
    settings_frame: NotRequired[dict[int, int]]


class Http2ResultData(TypedDict):
    protocol: str | None
    settings_count: int
    max_concurrent_streams: int


class Http2Result(TypedDict):
    name: str
    data: Http2ResultData
    confidence: float


class Http2FingerprintStrategy(FingerprintStrategy[Http2Data, Http2Result]):
    """Strategy for HTTP/2 & 3 fingerprinting."""

    name: str = "http2_3_stack"

    @beartype
    def extract(self, data: Http2Data) -> Http2Result:
        alpn = data.get("alpn")
        settings = data.get("settings_frame", {})

        # Heuristic analysis: ALPN + Settings
        # H2 is usually 'h2', H3 is usually 'h3'
        fingerprint: Http2ResultData = {
            "protocol": alpn,
            "settings_count": len(settings),
            "max_concurrent_streams": settings.get(3, 100),
        }

        confidence = 0.7 if alpn in ["h2", "h3"] else 0.2

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
