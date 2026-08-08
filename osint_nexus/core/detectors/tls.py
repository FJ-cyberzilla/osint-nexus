from typing import Any

from beartype import beartype

from osint_nexus.core.db.fingerprint_repository import FingerprintRepository


class TlsFingerprintStrategy:
    """Strategy for TLS (JA3) fingerprinting."""

    name: str = "tls_ja3"

    def __init__(self, repo: FingerprintRepository | None = None) -> None:
        self.repo = repo or FingerprintRepository()

    @beartype
    def extract(self, data: str) -> dict[str, Any]:
        # Expecting data to be the ja3 hash string
        ja3_hash = data

        device_info = self.repo.get_signature("ja3", ja3_hash) or "unknown"

        return {
            "name": self.name,
            "data": {
                "ja3_hash": ja3_hash,
                "inferred_device": device_info,
            },
            "confidence": 0.90 if device_info != "unknown" else 0.10,
        }
