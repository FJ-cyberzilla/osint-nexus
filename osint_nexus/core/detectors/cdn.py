from collections.abc import Mapping
from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue


class CdnFingerprintStrategy(FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]):
    """Strategy for CDN Header fingerprinting."""

    name: str = "cdn_headers"

    @beartype
    def extract(self, data: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
        # Expecting data: {"server_headers": dict[str, str]}
        headers_raw = data.get("server_headers")
        headers = headers_raw if isinstance(headers_raw, Mapping) else {}

        # Identify common CDN headers
        cdn_identified = "cf-ray" in headers or "x-amz-cf-id" in headers or "x-cache" in headers

        fingerprint: Mapping[str, JSONValue] = {
            "cdn_detected": cdn_identified,
            "provider": headers.get("server"),
        }

        confidence = 0.75 if cdn_identified else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
