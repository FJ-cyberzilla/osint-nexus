from collections.abc import Mapping

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue


class Http2FingerprintStrategy(FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]):
    """Strategy for HTTP/2 & 3 fingerprinting."""

    name: str = "http2_3_stack"

    @beartype
    def extract(self, data: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
        alpn = data.get("alpn")
        settings_raw = data.get("settings_frame")
        settings = settings_raw if isinstance(settings_raw, Mapping) else {}

        # Heuristic analysis: ALPN + Settings
        # H2 is usually 'h2', H3 is usually 'h3'
        fingerprint: Mapping[str, JSONValue] = {
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
