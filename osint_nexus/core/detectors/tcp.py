from typing import cast

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONObject, JSONValue


class TcpFingerprintStrategy(FingerprintStrategy[JSONValue, JSONObject]):
    """Strategy for TCP/IP stack fingerprinting (TTL/Window/Options)."""

    name: str = "tcp_stack"

    @beartype
    def extract(self, data: JSONValue) -> JSONObject:
        # Heuristic implementation, CC should be low (1 per block)
        data_obj = cast(JSONObject, data)
        ttl = cast(int, data_obj.get("ttl", 0))
        options = cast(list[str], data_obj.get("tcp_options", []))

        inferred_os, confidence = self._detect_os(ttl, options)

        return {
            "name": self.name,
            "data": {"inferred_os": inferred_os},
            "confidence": confidence,
        }

    def _detect_os(self, ttl: int, options: list[str]) -> tuple[str | None, float]:
        """Sub-method to maintain low CC."""
        if ttl == 128:
            return self._detect_windows(options)
        elif ttl == 64:
            return self._detect_linux_macos(options)
        elif ttl == 255:
            return "Network device (Cisco/Juniper)", 0.9
        return None, 0.0

    def _detect_windows(self, options: list[str]) -> tuple[str, float]:
        if "wscale" in options:
            return "Windows 10/11", 0.85
        return "Windows (older)", 0.7

    def _detect_linux_macos(self, options: list[str]) -> tuple[str, float]:
        if "timestamps" in options and "sack" in options:
            return "Linux (modern)", 0.75
        elif "timestamps" in options:
            return "macOS/iOS", 0.7
        return "Linux (older)", 0.5
