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
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

logger = logging.getLogger("osint_nexus.confidence")


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
    details: Dict[str, float] = field(default_factory=dict)

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
        self._platform_weights: Dict[str, float] = {
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
        self._thresholds: List[Tuple[float, str]] = [
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

    def calculate_confidence(
        self,
        found_platforms: Iterable[str],
        multipliers: Optional[Dict[str, float]] = None,
        additive_bonuses: Optional[Dict[str, float]] = None,
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

        # FIX #4: Deduplication & Validation
        clean_platforms: Set[str] = set()
        for p in found_platforms:
            if not isinstance(p, str) or not p.strip():
                raise ValueError(f"Invalid platform name provided: {p!r}")
            clean_platforms.add(p.strip().lower())

        detail: Dict[str, float] = {}
        total_weight = 0.0

        # 1. Base Weighted Sum
        for platform in clean_platforms:
            weight = self.get_platform_weight(platform)
            total_weight += weight
            detail[f"platform_{platform}"] = weight

        # 2. Normalise against fixed target (0–100)
        base_score = (total_weight / self._target_weight_for_max) * 100.0
        score = min(100.0, base_score) # Cap base score at 100
        detail["base_score_subtotal"] = score

        # FIX #2: Split Signals into Multipliers (Penalties) and Bonuses
        
        # 3. Apply Multipliers (Degradations like age, uncertainty)
        if multipliers:
            for signal, factor in multipliers.items():
                factor = max(0.0, factor) # Prevent negative multipliers
                if factor > 1.0:
                    logger.warning("Multiplier '%s' is > 1.0. Consider using additive_bonuses instead.", signal)
                score *= factor
                detail[f"multiplier_{signal}"] = factor

        # 4. Apply Additive Bonuses (Strong exact matches)
        if additive_bonuses:
            for signal, bonus in additive_bonuses.items():
                if bonus < 0:
                    logger.warning("Bonus '%s' is < 0. Consider using multipliers instead.", signal)
                score += bonus
                detail[f"bonus_{signal}"] = bonus

        # 5. Clamp final score strictly between 0 and 100
        final_score = max(0.0, min(100.0, score))

        # 6. Map to human-readable category
        category = "Minimal"
        for threshold, cat in self._thresholds:
            if final_score >= threshold:
                category = cat
                break

        logger.info(
            "Confidence: %.1f%% (%s) | %d platforms | Base Weight: %.1f",
            final_score,
            category,
            len(clean_platforms),
            total_weight
        )
        return ConfidenceResult(score=final_score, category=category, details=detail)

    # ------------------------------------------------------------------
    # Health check (for hierarchy integration)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Always healthy (stateless engine). Returns True."""
        return True
