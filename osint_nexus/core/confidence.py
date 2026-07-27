"""
Confidence engine for OSINT identity verification.

Provides a configurable, probabilistic scoring system that considers:
- Number of unique platforms where a username is found
- Platform-specific importance weights
- Degradation multipliers (e.g., stale data, low-res image)
- Additive bonuses (e.g., device fingerprint match, biometric match)
- Configurable score-to-category thresholds

Outputs a numeric score (0–100), a human‑readable category, and a
detailed breakdown for transparency.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field

logger = logging.getLogger("osint_nexus.confidence")


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
        score: Numeric confidence score (0.0–100.0). Higher is more confident.
        category: Human‑readable category (e.g., 'High', 'Medium', 'Low').
        details: Complete audit trail of contributing factors (base weights,
            multipliers, bonuses).
    """

    score: float
    category: str
    details: dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return a compact string suitable for terminal reports."""
        return f"{self.category} Confidence ({self.score:.1f}%)"


class ConfidenceEngine:
    """
    Calculates identity confidence based on platform presence and signals.

    This engine evaluates found platforms against a fixed "target weight" to
    determine a base score, preventing the score from degrading as the overall
    database of known platforms grows. It then applies modifiers:
    - Multipliers: To degrade confidence (e.g., age of account = 0.8)
    - Additive Bonuses: To boost confidence (e.g., exact device match = +25.0)
    """

    def __init__(self) -> None:
        # Default platform weights – higher means stronger identity signal.
        self._platform_weights: dict[str, float] = {
            "linkedin": 12.0,
            "github": 10.0,
            "facebook": 9.0,
            "twitter": 8.0,
            "instagram": 7.0,
            "reddit": 6.0,
            "aparat": 5.0,
            "generic": 3.0,
        }
        self._default_weight = 5.0

        # FIX #1: The Denominator Problem.
        # We define an absolute threshold that represents "100% Base Confidence".
        # E.g., Finding them on LinkedIn(12) + GitHub(10) + Twitter(8) = 30 points.
        self._target_weight_for_max = 30.0

        # Thresholds for category assignment (score >= threshold -> category)
        self._thresholds: list[tuple[float, str]] = [
            (85.0, "High"),
            (60.0, "Medium"),
            (30.0, "Low"),
            (0.0, "Minimal"),
        ]

    # ------------------------------------------------------------------
    # Public configuration methods
    # ------------------------------------------------------------------

    def set_platform_weight(self, platform: str, weight: float) -> None:
        """Override the importance weight for a specific platform."""
        if weight < 0:
            raise ValueError("Platform weight must be non‑negative.")
        self._platform_weights[platform.strip().lower()] = weight
        logger.debug("Platform weight set: %s -> %.1f", platform, weight)

    def get_platform_weight(self, platform: str) -> float:
        """Return the configured weight for a platform, or the default."""
        return self._platform_weights.get(platform.strip().lower(), self._default_weight)

    def set_target_weight(self, target: float) -> None:
        """Update the total weight required to achieve a 100% base score."""
        if target <= 0:
            raise ValueError("Target weight must be strictly positive.")
        self._target_weight_for_max = target

    # ------------------------------------------------------------------
    # Core calculation
    # ------------------------------------------------------------------

    def _get_base_score(self, clean_platforms: set[str], detail: dict[str, float]) -> tuple[float, float]:
        total_weight = 0.0
        for platform in clean_platforms:
            weight = self.get_platform_weight(platform)
            total_weight += weight
            detail[f"platform_{platform}"] = weight

        base_score = (total_weight / self._target_weight_for_max) * 100.0
        detail["base_score_subtotal"] = base_score
        return base_score, total_weight

    def _apply_factors(self, score: float, factors: list[Factor], detail: dict[str, float]) -> float:
        """Apply a list of pre-validated factors to the score."""
        for factor in factors:
            if factor.factor_type == "multiplier":
                score *= factor.value
                detail[f"multiplier_{factor.name}"] = factor.value
            elif factor.factor_type == "bonus":
                score += factor.value
                detail[f"bonus_{factor.name}"] = factor.value
        return score

    def _get_category(self, score: float) -> str:
        for threshold, cat in self._thresholds:
            if score >= threshold:
                return cat
        return "Minimal"

    def _create_factors(
        self, multipliers: dict[str, float] | None, additive_bonuses: dict[str, float] | None
    ) -> list[Factor]:
        """Convert and validate modifiers into Factor objects."""
        factors: list[Factor] = []
        if multipliers:
            for name, val in multipliers.items():
                factors.append(Factor(name=name, value=val, factor_type="multiplier"))

        if additive_bonuses:
            for name, val in additive_bonuses.items():
                factors.append(Factor(name=name, value=val, factor_type="bonus"))
        return factors

    def _clean_platforms(self, found_platforms: Iterable[str]) -> set[str]:
        """Validate and clean platform names."""
        clean_platforms: set[str] = set()
        for p in found_platforms:
            if not isinstance(p, str) or not p.strip():
                raise ValueError(f"Invalid platform name provided: {p!r}")
            clean_platforms.add(p.strip().lower())
        return clean_platforms

    def _log_result(self, final_score: float, category: str, num_platforms: int, total_weight: float) -> None:
        """Log the confidence result."""
        logger.info(
            "Confidence: %.1f%% (%s) | %d platforms | Base Weight: %.1f",
            final_score,
            category,
            num_platforms,
            total_weight,
        )

    def calculate_confidence(
        self,
        found_platforms: Iterable[str],
        multipliers: dict[str, float] | None = None,
        additive_bonuses: dict[str, float] | None = None,
    ) -> ConfidenceResult:
        """
        Compute the confidence score based on detected platforms and signals.

        Args:
            found_platforms: Iterable of platform names where the username was found.
                Duplicates will be automatically removed.
            multipliers: Optional dict of penalties. Used to DEGRADE the score.
                Values should be between 0.0 and 1.0 (e.g., {'dormant_account': 0.5})
            additive_bonuses: Optional dict of bonuses. Used to BOOST the score.
                Values are flat percentage points (e.g., {'device_fingerprint': 25.0})

        Returns:
            ConfidenceResult with numeric score, category, and audit details.
        """
        if not found_platforms:
            return ConfidenceResult(score=0.0, category="None")

        clean_platforms = self._clean_platforms(found_platforms)
        detail: dict[str, float] = {}

        score, total_weight = self._get_base_score(clean_platforms, detail)

        # Convert and validate modifiers into Factor objects
        factors = self._create_factors(multipliers, additive_bonuses)

        if factors:
            score = self._apply_factors(score, factors, detail)

        final_score = max(0.0, min(100.0, score))
        category = self._get_category(final_score)

        self._log_result(final_score, category, len(clean_platforms), total_weight)

        return ConfidenceResult(score=final_score, category=category, details=detail)

    # ------------------------------------------------------------------
    # Health check (for hierarchy integration)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Always healthy (stateless engine). Returns True."""
        return True
