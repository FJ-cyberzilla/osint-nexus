"""
Correlation Engine for identity matching.

Analyzes harvested identifiers to correlate usernames across platforms.
"""

from __future__ import annotations

import logging
from typing import NotRequired, TypedDict

logger = logging.getLogger(__name__)


class ResultMetadata(TypedDict, total=False):
    platform: str
    emails: list[str]
    links: list[str]


class AccountData(TypedDict):
    username: str
    type: str


class ConnectionData(TypedDict):
    email: NotRequired[str]
    phone: NotRequired[str]


class UserData(TypedDict):
    username: str
    accounts: list[AccountData]
    emails: list[ConnectionData]
    phones: list[ConnectionData]


class GraphNode(TypedDict):
    id: str
    type: str


class GraphEdge(TypedDict):
    source: str
    target: str
    type: str


class NetworkGraph(TypedDict):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class CorrelationEngine:
    """
    Correlates identities based on harvested secondary identifiers.
    """

    def __init__(self) -> None:
        """Initializes the CorrelationEngine."""
        pass

    async def correlate(self, results: list[ResultMetadata]) -> dict[str, list[str]]:
        """
        Analyzes a list of result metadata to find correlations.

        Args:
            results: List of result dictionaries.

        Returns:
            A dictionary mapping identifiers to platform lists.
        """
        correlation_map = self._build_correlation_map(results)
        correlations = self._filter_correlations(correlation_map)

        logger.debug("Correlations found: %s", correlations)
        return correlations

    def _build_correlation_map(self, results: list[ResultMetadata]) -> dict[str, list[str]]:
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

    def _filter_correlations(self, correlation_map: dict[str, list[str]]) -> dict[str, list[str]]:
        """Filters the correlation map to keep only identifiers found in multiple platforms."""
        return {k: v for k, v in correlation_map.items() if len(v) > 1}


class NodeGenerator:
    """Generates nodes for the relationship graph."""

    def generate(self, username_data: UserData) -> list[GraphNode]:
        """
        Generates graph nodes from username data.

        Args:
            username_data: Object containing username information and accounts.

        Returns:
            A list of node dictionaries.
        """
        nodes: list[GraphNode] = [{"id": username_data["username"], "type": "primary"}]
        nodes.extend(self._get_account_nodes(username_data))
        nodes.extend(self._get_email_nodes(username_data))
        nodes.extend(self._get_phone_nodes(username_data))
        return nodes

    def _get_account_nodes(self, username_data: UserData) -> list[GraphNode]:
        return [{"id": acc["username"], "type": acc["type"]} for acc in username_data["accounts"]]

    def _get_email_nodes(self, username_data: UserData) -> list[GraphNode]:
        return [{"id": conn["email"], "type": "email"} for conn in username_data["emails"] if "email" in conn]

    def _get_phone_nodes(self, username_data: UserData) -> list[GraphNode]:
        return [{"id": conn["phone"], "type": "phone"} for conn in username_data["phones"] if "phone" in conn]


class EdgeGenerator:
    """Generates edges for the relationship graph."""

    def generate(self, username_data: UserData) -> list[GraphEdge]:
        """
        Generates graph edges from username data.

        Args:
            username_data: Object containing username information and accounts.

        Returns:
            A list of edge dictionaries.
        """
        edges: list[GraphEdge] = []
        self._add_ownership_edges(edges, username_data)
        self._add_usage_edges(edges, username_data)
        self._add_interaction_edges(edges, username_data)
        return edges

    def _add_ownership_edges(self, edges: list[GraphEdge], data: UserData) -> None:
        """Adds ownership edges to the list of edges."""
        for acc in data["accounts"]:
            edges.append({"source": data["username"], "target": acc["username"], "type": "owns"})

    def _add_usage_edges(self, edges: list[GraphEdge], data: UserData) -> None:
        """Adds usage edges for email and phone."""
        for acc in data["accounts"]:
            self._add_email_edges_for_account(edges, acc, data["emails"])
            self._add_phone_edges_for_account(edges, acc, data["phones"])

    def _add_email_edges_for_account(self, edges: list[GraphEdge], acc: AccountData, emails: list[ConnectionData]) -> None:
        for conn in emails:
            if "email" in conn:
                edges.append({"source": acc["username"], "target": conn["email"], "type": "uses_email"})

    def _add_phone_edges_for_account(self, edges: list[GraphEdge], acc: AccountData, phones: list[ConnectionData]) -> None:
        for conn in phones:
            if "phone" in conn:
                edges.append({"source": acc["username"], "target": conn["phone"], "type": "uses_phone"})

    def _add_interaction_edges(self, edges: list[GraphEdge], data: UserData) -> None:
        """Adds interaction edges between accounts."""
        for acc1 in data["accounts"]:
            for acc2 in data["accounts"]:
                if acc1 != acc2:
                    edges.append(
                        {"source": acc1["username"], "target": acc2["username"], "type": "interacts"}
                    )


class RelationMapper:
    """Orchestrates relationship graph generation."""

    def __init__(self) -> None:
        """Initializes the RelationMapper."""
        self.node_gen = NodeGenerator()
        self.edge_gen = EdgeGenerator()

    def generate_network_graph(self, username_data: UserData) -> NetworkGraph:
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
