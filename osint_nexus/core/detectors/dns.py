from typing import cast

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class DnsFingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for DNS fingerprinting."""

    name: str = "dns_patterns"

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        # Expecting data: {"resolver_ip": str, "query_types": list[str]}
        data_obj = cast(JSONObject, data)
        resolver = data_obj.get("resolver_ip")
        query_types: list[str] = cast(list[str], data_obj.get("query_types", []))

        # Heuristic analysis: Resolver + Query pattern
        fingerprint: JSONObject = {
            "resolver": cast(str, resolver) if resolver else None,
            "query_type_count": len(set(query_types)),
            "supports_dnssec": "DNSSEC" in query_types,
        }

        confidence = 0.6 if resolver is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
