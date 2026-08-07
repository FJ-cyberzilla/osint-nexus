from dataclasses import dataclass, field


@dataclass
class ConfidenceConfig:
    platform_weights: dict[str, float] = field(
        default_factory=lambda: {
            "linkedin": 12.0,
            "github": 10.0,
            "facebook": 9.0,
            "twitter": 8.0,
            "instagram": 7.0,
            "reddit": 6.0,
            "aparat": 5.0,
            "generic": 3.0,
        }
    )
    default_weight: float = 5.0
    target_weight_for_max: float = 30.0
    thresholds: list[tuple[float, str]] = field(
        default_factory=lambda: [
            (85.0, "High"),
            (60.0, "Medium"),
            (30.0, "Low"),
            (0.0, "Minimal"),
        ]
    )
