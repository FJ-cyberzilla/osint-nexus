"""
Correlation Engine for identity matching.

Analyzes harvested identifiers to correlate usernames across platforms.
"""

from __future__ import annotations

import logging
from typing import Any

# Optional dependencies for advanced correlation
try:
    import imagehash  # noqa: F401
    from PIL import Image  # noqa: F401
    from rapidfuzz import fuzz  # noqa: F401

    HAS_CORRELATION_EXTRAS = True
except ImportError:
    HAS_CORRELATION_EXTRAS = False

logger = logging.getLogger("osint_nexus.core.correlation")


class CorrelationEngine:
    """
    Correlates identities based on harvested secondary identifiers.
    """

    def __init__(self) -> None:
        pass

    async def correlate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyzes a list of result metadata to find correlations.
        """
        correlation_map = self._build_correlation_map(results)
        self._log_correlation_extras_status()
        correlations = self._filter_correlations(correlation_map)

        logger.debug("Correlations found: %s", correlations)
        return correlations

    def _build_correlation_map(self, results: list[dict[str, Any]]) -> dict[str, list[str]]:
        correlation_map: dict[str, list[str]] = {}
        for result in results:
            platform = result.get("platform", "unknown")
            self._add_to_map(correlation_map, platform, "email", result.get("emails", []))
            self._add_to_map(correlation_map, platform, "link", result.get("links", []))
        return correlation_map

    def _add_to_map(self, cmap: dict, platform: str, prefix: str, items: list[str]) -> None:
        for item in items:
            cmap.setdefault(f"{prefix}:{item}", []).append(platform)

    def _log_correlation_extras_status(self) -> None:
        if not HAS_CORRELATION_EXTRAS:
            logger.warning(
                "Correlation extras (imagehash, Pillow, rapidfuzz) not installed. Advanced correlation disabled."
            )

    def _filter_correlations(self, correlation_map: dict[str, list[str]]) -> dict[str, list[str]]:
        return {k: v for k, v in correlation_map.items() if len(v) > 1}
