"""
Device fingerprinting and telemetry collection for OSINT scans.

Provides:
- Collection of scan environment metadata (proxy, user-agent, timestamp).
- Inference of target device / OS from provider response content.
- Configurable detection rules for extending device recognition.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.fingerprint")


@dataclass
class DeviceInfo:
    """Structured result of device fingerprint inference."""

    device_model: str = "Unknown"
    os_family: str = "Unknown"
    confidence: float = 0.0
    raw_matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "device_model": self.device_model,
            "os_family": self.os_family,
            "confidence": self.confidence,
            "matches": self.raw_matches,
        }


class FingerprintAgent:
    """
    Collects scan telemetry and infers target device characteristics.

    Device inference uses a priority-ordered list of regex patterns
    that can be customised via the configuration.

    Attributes:
        config: Optional configuration object for custom patterns.
    """

    # Default device detection rules: (pattern, device_model, os_family)
    DEFAULT_DEVICE_PATTERNS: list[tuple[str, str, str]] = [
        (r"iPhone", "iPhone", "iOS"),
        (r"iPad", "iPad", "iOS"),
        (r"iOS\s*\d+", "iOS Device", "iOS"),
        (r"Android\s*\d+", "Android Device", "Android"),
        (r"Windows\s*(?:NT|Phone|Mobile)", "Windows Device", "Windows"),
        (r"Mac\s*OS\s*X", "Mac", "macOS"),
        (r"Linux", "Linux Desktop", "Linux"),
        (r"CrOS", "Chromebook", "Chrome OS"),
    ]

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        # Load custom patterns from config if provided
        self._device_patterns = self._load_patterns()

    def collect_scan_telemetry(self, proxy: str | None, user_agent: str) -> dict[str, Any]:
        """
        Collect environment metadata for the current scan.

        Args:
            proxy: The proxy URL used (or None if direct).
            user_agent: The User-Agent string employed.

        Returns:
            A dictionary with proxy_node, agent_fingerprint, scan_timestamp.
            On failure, returns an error dict.
        """
        try:
            return {
                "proxy_node": proxy or "Direct (No Proxy)",
                "agent_fingerprint": user_agent,
                "scan_timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Telemetry collection failed: %s", exc, exc_info=True)
            return {"error": "Telemetry collection failed"}

    def infer_target_device(self, content: str) -> dict[str, Any]:
        """
        Infer the target's device model and OS from response content.

        Args:
            content: The HTML/text content from a provider's response.

        Returns:
            A dictionary with device_model, os_family (and extra fields).
            Backward compatible with the agent's current usage.
        """
        try:
            if not content:
                return DeviceInfo().to_dict()

            result = DeviceInfo()
            # Check patterns in order; first match wins (highest priority)
            for pattern, device, os_family in self._device_patterns:
                if pattern in content:  # simple substring match; could be regex in future
                    result.device_model = device
                    result.os_family = os_family
                    result.confidence = 0.8  # moderate confidence for substring
                    result.raw_matches.append(pattern)
                    # Stop at first match; most specific patterns are listed first
                    break

            return result.to_dict()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Device inference failed: %s", exc, exc_info=True)
            return DeviceInfo(device_model="Error", os_family="Error").to_dict()

    async def health_check(self) -> bool:
        """Fingerprint agent is stateless and always healthy."""
        return True

    def _load_patterns(self) -> list[tuple[str, str, str]]:
        """Merge default patterns with any custom patterns from config."""
        custom = getattr(self.config, "DEVICE_PATTERNS", None)
        if not custom or not isinstance(custom, list):
            return self.DEFAULT_DEVICE_PATTERNS
        # Custom patterns should have the same structure: (regex, model, os)
        # Prepend custom patterns so they take priority
        validated = []
        for entry in custom:
            if isinstance(entry, (list, tuple)) and len(entry) == 3:
                validated.append(tuple(entry))
        return validated + self.DEFAULT_DEVICE_PATTERNS
