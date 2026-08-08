from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from osint_nexus.core.type_defs import JSONObject

if TYPE_CHECKING:
    # Avoid circular imports
    pass


@dataclass
class Factor:
    """
    Represents a scoring modifier (either a multiplier or a bonus)
    for the ConfidenceEngine, incorporating strict validation.
    """

    name: str
    value: float
    factor_type: str  # must be "multiplier" or "bonus"

    def __post_init__(self) -> None:
        self._validate_meta()
        self._validate_value()

    def _validate_meta(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Factor name must be a non-empty string.")
        if self.factor_type not in ("multiplier", "bonus"):
            raise ValueError("Factor type must be either 'multiplier' or 'bonus'.")

    def _validate_value(self) -> None:
        if self.factor_type == "multiplier" and not (0.0 <= self.value <= 1.0):
            raise ValueError(f"Multiplier '{self.name}' must be between 0.0 and 1.0, got {self.value}")
        if self.factor_type == "bonus" and self.value < 0.0:
            raise ValueError(f"Bonus '{self.name}' must be non-negative, got {self.value}")


@dataclass
class ConfidenceResult:
    """
    Encapsulates the result of a confidence calculation.

    Attributes:
        score: Numeric confidence score (0.0-100.0). Higher is more confident.
        category: Human-readable category (e.g., 'High', 'Medium', 'Low').
        details: Complete audit trail of contributing factors (base weights,
            multipliers, bonuses).
    """

    score: float
    category: str
    details: dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return a compact string suitable for terminal reports."""
        return f"{self.category} Confidence ({self.score:.1f}%)"


@dataclass
class Account:
    id: str
    username: str | None = None
    platform: str | None = None


@dataclass
class IdentityProfile:
    username: str
    accounts: list[Account]
    relationships: RelationshipGraph
    timeline: Timeline | None
    correlations: Correlations | None
    confidence_score: float


@dataclass
class RelationshipGraph:
    nodes: list[JSONObject]
    edges: list[JSONObject]


@dataclass
class Timeline:
    events: list[JSONObject]


@dataclass
class Correlations:
    data: JSONObject


class Neo4jConnection:
    def add_relationship(self, rel_type: str, account: Account) -> None:
        pass


class LLMInterface:
    pass


class TemporalAnalysis:
    def create_timeline(self, accounts: list[Account]) -> Timeline:
        return Timeline(events=[])
