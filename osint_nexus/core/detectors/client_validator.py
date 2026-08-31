from collections.abc import Mapping
from typing import TypedDict

from beartype import beartype

from osint_nexus.core.type_defs import JSONObject


class ClientMetricsData(TypedDict):
    font_fp: str | None
    canvas_hash: str | None
    suspicious: bool


class ClientMetricsResult(TypedDict):
    name: str
    data: ClientMetricsData
    confidence: float


class ClientFingerprintValidator:
    """Validator for client-side rendered metrics (Technique 9)."""

    name: str = "client_metrics"

    @beartype
    def extract(self, data: JSONObject) -> ClientMetricsResult:
        # Expecting data: {"font_fingerprint": str, "canvas_hash": str}
        if not isinstance(data, Mapping):
            return {
                "name": self.name,
                "data": {"font_fp": None, "canvas_hash": None, "suspicious": False},
                "confidence": 0.0,
            }

        font_fp = data.get("font_fingerprint")
        canvas_hash = data.get("canvas_hash")

        # Ensure correct types for TypedDict
        font_fp_str = str(font_fp) if font_fp is not None else None
        canvas_hash_str = str(canvas_hash) if canvas_hash is not None else None

        # Simple heuristic for suspicion
        is_suspicious = canvas_hash == "webgl-disabled" or font_fp == "Arial"

        # Heuristic: metrics mismatch usually indicates spoofing/automation
        fingerprint: ClientMetricsData = {
            "font_fp": font_fp_str,
            "canvas_hash": canvas_hash_str,
            "suspicious": is_suspicious,
        }

        confidence = 0.5 if font_fp is not None and canvas_hash is not None else 0.1

        return {
            "name": self.name,
            "data": fingerprint,
            "confidence": confidence,
        }
