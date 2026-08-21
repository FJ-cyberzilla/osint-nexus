from typing import cast

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class TimezoneFingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for Timezone/NTP fingerprinting."""

    name: str = "timezone_ntp"

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        # Expecting data: {"timezone": str, "offset_seconds": int}
        data_obj = cast(JSONObject, data)
        tz = data_obj.get("timezone")
        offset = data_obj.get("offset_seconds", 0)

        # Ensure types for dictionary content
        tz_str = str(tz) if tz is not None else "unknown"
        offset_int = int(cast(int, offset))

        # Heuristic analysis
        fingerprint = {
            "timezone": tz_str,
            "offset_seconds": offset_int,
        }

        confidence = 0.5 if tz is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": float(confidence),
        }
