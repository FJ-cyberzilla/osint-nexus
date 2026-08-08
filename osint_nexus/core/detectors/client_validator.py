from typing import Any

from beartype import beartype


class ClientFingerprintValidator:
    """Validator for client-side rendered metrics (Technique 9)."""

    name: str = "client_metrics"

    @beartype
    def extract(self, data: Any) -> dict[str, Any]:
        # Expecting data: {"font_fingerprint": str, "canvas_hash": str}
        if not isinstance(data, dict):
            return {"name": self.name, "data": {}, "confidence": 0.0}

        font_fp = data.get("font_fingerprint")
        canvas_hash = data.get("canvas_hash")

        # Heuristic: metrics mismatch usually indicates spoofing/automation
        fingerprint = {
            "font_fp": font_fp,
            "canvas_hash": canvas_hash,
        }

        confidence = 0.5 if font_fp is not None and canvas_hash is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
