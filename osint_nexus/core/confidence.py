from __future__ import annotations

import logging
from collections.abc import Iterable

from .confidence_config import ConfidenceConfig
from .models import ConfidenceResult, Factor

logger = logging.getLogger("osint_nexus.confidence")


class ConfidenceEngine:
    """
    Calculates identity confidence based on platform presence and signals.
    """

    def __init__(self) -> None:
        from osint_nexus.core.score_calculator import ScoreCalculator

        self.config = ConfidenceConfig()
        self.calculator = ScoreCalculator(self.config)

    # ------------------------------------------------------------------
    # Public configuration methods
    # ------------------------------------------------------------------

    def set_platform_weight(self, platform: str, weight: float) -> None:
        """Override the importance weight for a specific platform."""
        if weight < 0:
            raise ValueError("Platform weight must be non‑negative.")
        self.config.platform_weights[platform.strip().lower()] = weight
        logger.debug("Platform weight set: %s -> %.1f", platform, weight)

    def get_platform_weight(self, platform: str) -> float:
        """Return the configured weight for a platform, or the default."""
        return self.calculator.get_platform_weight(platform)

    def set_target_weight(self, target: float) -> None:
        """Update the total weight required to achieve a 100% base score."""
        if target <= 0:
            raise ValueError("Target weight must be strictly positive.")
        self.config.target_weight_for_max = target

    # ------------------------------------------------------------------
    # Core calculation
    # ------------------------------------------------------------------

    def _apply_factors(self, score: float, factors: list[Factor], detail: dict[str, float]) -> float:
        """Apply a list of pre-validated factors to the score."""
        return self.calculator.apply_factors(score, factors, detail)

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

        score, total_weight = self.calculator.calculate_base_score(clean_platforms, detail)

        # Convert and validate modifiers into Factor objects
        factors = self._create_factors(multipliers, additive_bonuses)

        if factors:
            score = self.calculator.apply_factors(score, factors, detail)

        final_score = max(0.0, min(100.0, score))
        category = self.calculator.get_category(final_score)

        self._log_result(final_score, category, len(clean_platforms), total_weight)

        return ConfidenceResult(score=final_score, category=category, details=detail)

    # ------------------------------------------------------------------
    # Health check (for hierarchy integration)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Always healthy (stateless engine). Returns True."""
        return True
