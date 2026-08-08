from typing import Any

from beartype import beartype


class TimezoneFingerprintStrategy:
    """Strategy for Timezone/NTP fingerprinting."""

    name: str = "timezone_ntp"

    @beartype
    def extract(self, data: dict[str, Any]) -> dict[str, Any]:
        # Expecting data: {"timezone": str, "offset_seconds": int}
        tz = data.get("timezone")
        offset = data.get("offset_seconds", 0)

        # Ensure types for dictionary content
        tz_str = str(tz) if tz is not None else "unknown"
        offset_int = int(offset)

        # Heuristic analysis
        fingerprint: dict[str, str | int] = {
            "timezone": tz_str,
            "offset_seconds": offset_int,
        }

        confidence = 0.5 if tz is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": float(confidence),
        }
