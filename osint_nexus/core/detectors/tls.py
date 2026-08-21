from typing import cast

from beartype import beartype

from osint_nexus.core.db.fingerprint_repository import FingerprintRepository
from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class TlsFingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for TLS (JA3) fingerprinting."""

    name: str = "tls_ja3"

    def __init__(self, repo: FingerprintRepository | None = None) -> None:
        self.repo = repo or FingerprintRepository()

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        # Expecting data to be a dictionary containing the ja3 hash string
        data_obj = cast(JSONObject, data)
        ja3_hash = cast(str, data_obj.get("ja3_hash", "unknown"))

        device_info = self.repo.get_signature("ja3", ja3_hash) or "unknown"

        return {
            "name": self.name,
            "data": {
                "ja3_hash": ja3_hash,
                "inferred_device": device_info,
            },
            "confidence": 0.90 if device_info != "unknown" else 0.10,
        }
