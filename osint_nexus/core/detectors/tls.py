from collections.abc import Mapping
from beartype import beartype

from osint_nexus.core.db.fingerprint_repository import FingerprintRepository
from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue


class TlsFingerprintStrategy(FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]):
    """Strategy for TLS (JA3) fingerprinting."""

    name: str = "tls_ja3"

    def __init__(self, repo: FingerprintRepository | None = None) -> None:
        self.repo = repo or FingerprintRepository()

    @beartype
    def extract(self, data: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
        # Expecting data to be a dictionary containing the ja3 hash string
        ja3_hash = str(data.get("ja3_hash", "unknown"))

        device_info = self.repo.get_signature("ja3", ja3_hash) or "unknown"

        return {
            "name": self.name,
            "data": {
                "ja3_hash": ja3_hash,
                "inferred_device": device_info,
            },
            "confidence": 0.90 if device_info != "unknown" else 0.10,
        }
