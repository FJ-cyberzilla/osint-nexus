from typing import Any

from beartype import beartype


class ExtensionFingerprintStrategy:
    """Strategy for Browser Extension fingerprinting."""

    name: str = "extension_load"

    @beartype
    def extract(self, data: Any) -> dict[str, Any]:
        # Expecting data: {"detected_extensions": list[str]}
        if not isinstance(data, dict):
            return {"name": self.name, "data": {}, "confidence": 0.0}

        extensions = data.get("detected_extensions", [])

        # Heuristic: analyze extension load order or set
        has_adblocker = any("adblock" in e.lower() or "ublock" in e.lower() for e in extensions)

        fingerprint = {
            "extension_count": len(extensions),
            "has_adblocker": has_adblocker,
        }

        confidence = 0.8 if len(extensions) > 0 else 0.2

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
