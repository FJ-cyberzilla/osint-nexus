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
        """Initializes the CorrelationEngine."""
        pass

    async def correlate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyzes a list of result metadata to find correlations.

        Args:
            results: List of result dictionaries.

        Returns:
            A dictionary mapping identifiers to platform lists.
        """
        correlation_map = self._build_correlation_map(results)
        self._log_correlation_extras_status()
        correlations = self._filter_correlations(correlation_map)

        logger.debug("Correlations found: %s", correlations)
        return correlations

    def _build_correlation_map(self, results: list[dict[str, Any]]) -> dict[str, list[str]]:
        """Builds a map of identifiers to the platforms where they were found."""
        correlation_map: dict[str, list[str]] = {}
        for result in results:
            platform = result.get("platform", "unknown")
            self._add_to_map(correlation_map, platform, "email", result.get("emails", []))
            self._add_to_map(correlation_map, platform, "link", result.get("links", []))
        return correlation_map

    def _add_to_map(self, cmap: dict[str, list[str]], platform: str, prefix: str, items: list[str]) -> None:
        """Adds identifiers to the correlation map."""
        for item in items:
            cmap.setdefault(f"{prefix}:{item}", []).append(platform)

    def _log_correlation_extras_status(self) -> None:
        """Logs the availability of optional correlation dependencies."""
        if not HAS_CORRELATION_EXTRAS:
            logger.warning(
                "Correlation extras (imagehash, Pillow, rapidfuzz) not installed. Advanced correlation disabled."
            )

    def _filter_correlations(self, correlation_map: dict[str, list[str]]) -> dict[str, list[str]]:
        """Filters the correlation map to keep only identifiers found in multiple platforms."""
        return {k: v for k, v in correlation_map.items() if len(v) > 1}


class NodeGenerator:
    """Generates nodes for the relationship graph."""

    def generate(self, username_data: Any) -> list[dict[str, str]]:
        """
        Generates graph nodes from username data.

        Args:
            username_data: Object containing username information and accounts.

        Returns:
            A list of node dictionaries.
        """
        nodes = [{"id": username_data.username, "type": "primary"}]
        nodes.extend([{"id": acc.username, "type": acc.type} for acc in username_data.accounts])
        nodes.extend([{"id": conn.email, "type": "email"} for conn in username_data.emails])
        nodes.extend([{"id": conn.phone, "type": "phone"} for conn in username_data.phones])
        return nodes


class EdgeGenerator:
    """Generates edges for the relationship graph."""

    def generate(self, username_data: Any) -> list[dict[str, str]]:
        """
        Generates graph edges from username data.

        Args:
            username_data: Object containing username information and accounts.

        Returns:
            A list of edge dictionaries.
        """
        edges: list[dict[str, str]] = []
        self._add_ownership_edges(edges, username_data)
        self._add_usage_edges(edges, username_data)
        self._add_interaction_edges(edges, username_data)
        return edges

    def _add_ownership_edges(self, edges: list[dict[str, str]], data: Any) -> None:
        """Adds ownership edges to the list of edges."""
        for acc in data.accounts:
            edges.append({"source": data.username, "target": acc.username, "type": "owns"})

    def _add_usage_edges(self, edges: list[dict[str, str]], data: Any) -> None:
        """Adds usage edges for email and phone."""
        for acc in data.accounts:
            for conn in data.emails:
                edges.append({"source": acc.username, "target": conn.email, "type": "uses_email"})
            for conn in data.phones:
                edges.append({"source": acc.username, "target": conn.phone, "type": "uses_phone"})

    def _add_interaction_edges(self, edges: list[dict[str, str]], data: Any) -> None:
        """Adds interaction edges between accounts."""
        for acc1 in data.accounts:
            for acc2 in data.accounts:
                if acc1 != acc2:
                    edges.append({"source": acc1.username, "target": acc2.username, "type": "interacts"})


class RelationMapper:
    """Orchestrates relationship graph generation."""

    def __init__(self) -> None:
        """Initializes the RelationMapper."""
        self.node_gen = NodeGenerator()
        self.edge_gen = EdgeGenerator()

    def generate_network_graph(self, username_data: Any) -> dict[str, Any]:
        """
        Generates a network graph based on username data.

        Args:
            username_data: Object containing username information and accounts.

        Returns:
            A dictionary containing nodes and edges of the graph.
        """
        return {
            "nodes": self.node_gen.generate(username_data),
            "edges": self.edge_gen.generate(username_data),
        }
