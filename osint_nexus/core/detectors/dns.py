from collections.abc import Mapping
from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue


class DnsFingerprintStrategy(FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]):
    """Strategy for DNS fingerprinting."""

    name: str = "dns_patterns"

    @beartype
    def extract(self, data: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
        # Expecting data: {"resolver_ip": str, "query_types": list[str]}
        resolver = data.get("resolver_ip")
        query_types_raw = data.get("query_types")
        query_types: list[str] = query_types_raw if isinstance(query_types_raw, list) else []

        # Heuristic analysis: Resolver + Query pattern
        fingerprint: Mapping[str, JSONValue] = {
            "resolver": str(resolver) if isinstance(resolver, str) else None,
            "query_type_count": len(set(query_types)),
            "supports_dnssec": "DNSSEC" in query_types,
        }

        confidence = 0.6 if resolver is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
