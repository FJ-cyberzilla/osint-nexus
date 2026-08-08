from typing import Any

from beartype import beartype


class DnsFingerprintStrategy:
    """Strategy for DNS fingerprinting."""

    name: str = "dns_patterns"

    @beartype
    def extract(self, data: Any) -> dict[str, Any]:
        # Expecting data: {"resolver_ip": str, "query_types": list[str]}
        if not isinstance(data, dict):
            return {"name": self.name, "data": {}, "confidence": 0.0}

        resolver = data.get("resolver_ip")
        query_types = data.get("query_types", [])

        # Heuristic analysis: Resolver + Query pattern
        fingerprint = {
            "resolver": resolver,
            "query_type_count": len(set(query_types)),
            "supports_dnssec": "DNSSEC" in query_types,
        }

        confidence = 0.6 if resolver is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
