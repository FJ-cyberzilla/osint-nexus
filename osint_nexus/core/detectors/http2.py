from typing import cast

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class Http2FingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for HTTP/2 & 3 fingerprinting."""

    name: str = "http2_3_stack"

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        data_obj = cast(JSONObject, data)
        alpn = data_obj.get("alpn")
        settings = cast(dict[int, int], data_obj.get("settings_frame", {}))

        # Heuristic analysis: ALPN + Settings
        # H2 is usually 'h2', H3 is usually 'h3'
        fingerprint: JSONObject = {
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
