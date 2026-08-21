from typing import cast

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class ExtensionFingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for Browser Extension fingerprinting."""

    name: str = "extension_load"

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        # Expecting data: {"detected_extensions": list[str]}
        data_obj = cast(JSONObject, data)
        extensions: list[str] = cast(list[str], data_obj.get("detected_extensions", []))

        # Heuristic: analyze extension load order or set
        has_adblocker = any("adblock" in e.lower() or "ublock" in e.lower() for e in extensions)

        fingerprint: JSONObject = {
            "extension_count": len(extensions),
            "has_adblocker": has_adblocker,
        }

        confidence = 0.8 if len(extensions) > 0 else 0.2

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
