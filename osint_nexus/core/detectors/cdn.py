from typing import cast

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class CdnFingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for CDN Header fingerprinting."""

    name: str = "cdn_headers"

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        # Expecting data: {"server_headers": dict[str, str]}
        data_obj = cast(JSONObject, data)
        headers: dict[str, str] = cast(dict[str, str], data_obj.get("server_headers", {}))

        # Identify common CDN headers
        cdn_identified = "cf-ray" in headers or "x-amz-cf-id" in headers or "x-cache" in headers

        fingerprint: JSONObject = {
            "cdn_detected": cdn_identified,
            "provider": headers.get("server"),
        }

        confidence = 0.75 if cdn_identified else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
