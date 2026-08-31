"""
Device fingerprinting and telemetry collection for OSINT scans.

Provides:
- Collection of scan environment metadata (proxy, user-agent, timestamp).
- Inference of target device / OS from provider response content.
- Configurable detection rules for extending device recognition.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast

from osint_nexus.core.config import Config
from osint_nexus.core.constants import DeviceInferenceConstants
from osint_nexus.core.detectors.cdn import CdnFingerprintStrategy
from osint_nexus.core.detectors.dns import DnsFingerprintStrategy
from osint_nexus.core.detectors.extensions import ExtensionFingerprintStrategy
from osint_nexus.core.detectors.http import HttpFingerprintStrategy
from osint_nexus.core.detectors.http2 import Http2FingerprintStrategy
from osint_nexus.core.detectors.registry import FingerprintStrategyRegistry
from osint_nexus.core.detectors.tcp import TcpFingerprintStrategy
from osint_nexus.core.detectors.timezone import TimezoneFingerprintStrategy
from osint_nexus.core.detectors.tls import TlsFingerprintStrategy
from osint_nexus.core.exceptions import NexusError
from osint_nexus.core.fingerprint_decider import ClientFingerprintValidator as ComprehensiveValidator
from osint_nexus.core.type_defs import JSONValue, to_json_value

logger = logging.getLogger("osint_nexus.fingerprint")


@dataclass
class DeviceInfo:
    """Structured result of device fingerprint inference."""

    device_model: str | None = None
    os_family: str | None = None
    confidence: float = DeviceInferenceConstants.MIN_CONFIDENCE
    raw_matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert to dictionary for backward compatibility."""
        return {
            "device_model": self.device_model or DeviceInferenceConstants.UNIDENTIFIED,
            "os_family": self.os_family or DeviceInferenceConstants.UNIDENTIFIED,
            "confidence": self.confidence,
            "matches": cast(list[JSONValue], self.raw_matches),
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

    def __init__(self, config: Config | None = None, ja3_hash: str | None = None) -> None:
        self.config = config or Config()
        self.ja3_hash = ja3_hash
        # Load custom patterns from config if provided
        self._device_patterns = self._load_patterns()

        # New: Orchestration of strategies
        self.registry = FingerprintStrategyRegistry()
        self.registry.register(HttpFingerprintStrategy())
        self.registry.register(TcpFingerprintStrategy())
        self.registry.register(TlsFingerprintStrategy())
        self.registry.register(DnsFingerprintStrategy())
        self.registry.register(CdnFingerprintStrategy())
        self.registry.register(ExtensionFingerprintStrategy())
        self.registry.register(Http2FingerprintStrategy())
        self.registry.register(TimezoneFingerprintStrategy())
        self.registry.register(ComprehensiveValidator())

    def collect_all_fingerprints(self, data: Mapping[str, JSONValue]) -> dict[str, JSONValue]:
        """Aggregate results from all registered strategies."""
        results: dict[str, JSONValue] = {}
        confidence_scores: list[float] = []

        # If JA3 hash is present, inject/override for TlsFingerprintStrategy
        strategy_data = data
        if self.ja3_hash:
            # We must be careful about how strategies expect data.
            # TlsFingerprintStrategy.extract() expects a string if it's the direct JA3 hash.
            # But here, we might need to update the data dictionary for the TLS strategy specifically.
            pass

        for strategy in self.registry.get_all():
            try:
                # Specific override for TLS strategy
                if strategy.name == "tls_ja3" and self.ja3_hash:
                    # TlsFingerprintStrategy.extract() needs Mapping, so we wrap ja3_hash
                    res = strategy.extract({"ja3_hash": to_json_value(self.ja3_hash)})
                else:
                    res = strategy.extract(strategy_data)

                results[strategy.name] = res["data"]
                confidence_scores.append(float(res.get("confidence", 0.0)))
            except Exception as exc:
                logger.warning("Strategy %s failed: %s", strategy.name, exc)

        # Simple combined confidence score calculation
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        return {
            "fingerprints": results,
            "combined_confidence": avg_confidence,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def collect_scan_telemetry(self, proxy: str | None, user_agent: str) -> dict[str, JSONValue]:
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
        except NexusError as exc:
            logger.error("Telemetry collection failed: %s", exc, exc_info=True)
            return {"error": "Telemetry collection failed"}

    def infer_target_device(self, content: JSONValue) -> dict[str, JSONValue]:
        """
        Infer the target's device model and OS from response content.

        Args:
            content: The HTML/text content from a provider's response.

        Returns:
            A dictionary with device_model, os_family (and extra fields).
            Backward compatible with the agent's current usage.
        """
        try:
            if not isinstance(content, str) or not content:
                return DeviceInfo().to_dict()

            result = DeviceInfo()
            # Check patterns in order; first match wins (highest priority)
            for pattern, device, os_family in self._device_patterns:
                if re.search(pattern, content):
                    result.device_model = device
                    result.os_family = os_family
                    result.confidence = (
                        DeviceInferenceConstants.REGEX_MATCH_CONFIDENCE
                    )  # moderate confidence for regex
                    result.raw_matches.append(pattern)
                    # Stop at first match; most specific patterns are listed first
                    break

            return result.to_dict()
        except Exception as exc:
            logger.error("Device inference failed: %s", exc, exc_info=True)
            return DeviceInfo(
                device_model=DeviceInferenceConstants.UNKNOWN, os_family=DeviceInferenceConstants.UNKNOWN
            ).to_dict()

    async def health_check(self) -> bool:
        """Fingerprint agent is stateless and always healthy."""
        return True

    def _load_patterns(self) -> list[tuple[str, str, str]]:
        """Merge default patterns with any custom patterns from config."""
        custom = getattr(self.config, "device_patterns", [])
        if not isinstance(custom, list):
            return self.DEFAULT_DEVICE_PATTERNS

        validated = [tuple(entry) for entry in custom if isinstance(entry, (list, tuple)) and len(entry) == 3]
        return validated + self.DEFAULT_DEVICE_PATTERNS
