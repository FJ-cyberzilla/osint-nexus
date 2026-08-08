from typing import Any

from beartype import beartype


class CdnFingerprintStrategy:
    """Strategy for CDN Header fingerprinting."""

    name: str = "cdn_headers"

    @beartype
    def extract(self, data: Any) -> dict[str, Any]:
        # Expecting data: {"server_headers": dict[str, str]}
        if not isinstance(data, dict):
            return {"name": self.name, "data": {}, "confidence": 0.0}

        headers = data.get("server_headers", {})

        # Identify common CDN headers
        cdn_identified = "cf-ray" in headers or "x-amz-cf-id" in headers or "x-cache" in headers

        fingerprint = {
            "cdn_detected": cdn_identified,
            "provider": headers.get("server"),
        }

        confidence = 0.75 if cdn_identified else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
