from dataclasses import dataclass

from osint_nexus.core.confidence_config import ConfidenceConfig
from osint_nexus.core.models import Factor


@dataclass
class ScoreCalculator:
    config: ConfidenceConfig

    def get_platform_weight(self, platform: str) -> float:
        """Return the configured weight for a platform, or the default."""
        return self.config.platform_weights.get(platform.strip().lower(), self.config.default_weight)

    def calculate_base_score(
        self, clean_platforms: set[str], detail: dict[str, float]
    ) -> tuple[float, float]:
        total_weight = 0.0
        for platform in clean_platforms:
            weight = self.get_platform_weight(platform)
            total_weight += weight
            detail[f"platform_{platform}"] = weight

        base_score = (total_weight / self.config.target_weight_for_max) * 100.0
        detail["base_score_subtotal"] = base_score
        return base_score, total_weight

    def apply_factors(self, score: float, factors: list[Factor], detail: dict[str, float]) -> float:
        """Apply a list of pre-validated factors to the score."""
        for factor in factors:
            if factor.factor_type == "multiplier":
                score *= factor.value
                detail[f"multiplier_{factor.name}"] = factor.value
            elif factor.factor_type == "bonus":
                score += factor.value
                detail[f"bonus_{factor.name}"] = factor.value
        return score

    def get_category(self, score: float) -> str:
        for threshold, cat in self.config.thresholds:
            if score >= threshold:
                return cat
        return "Minimal"
