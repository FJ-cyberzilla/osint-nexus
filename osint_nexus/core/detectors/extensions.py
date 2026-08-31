from collections.abc import Mapping
from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue


class ExtensionFingerprintStrategy(FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]):
    """Strategy for Browser Extension fingerprinting."""

    name: str = "extension_load"

    @beartype
    def extract(self, data: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
        # Expecting data: {"detected_extensions": list[str]}
        extensions_raw = data.get("detected_extensions")
        extensions = extensions_raw if isinstance(extensions_raw, list) else []

        # Heuristic: analyze extension load order or set
        has_adblocker = any(
            isinstance(e, str) and ("adblock" in e.lower() or "ublock" in e.lower()) for e in extensions
        )

        fingerprint: Mapping[str, JSONValue] = {
            "extension_count": len(extensions),
            "has_adblocker": has_adblocker,
        }

        confidence = 0.8 if len(extensions) > 0 else 0.2

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
