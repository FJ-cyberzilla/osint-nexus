from dataclasses import dataclass


@dataclass
class EvasionWeights:
    ai_signature: float = 0.2
    headless_mode: float = 0.3
    webdriver_active: float = 0.3
    automation_plugins: float = 0.3
    platform_density_penalty: float = 0.1
    degraded_pipeline_penalty: float = 0.2
    platform_density_threshold: int = 5
    novel_detector_weight: float = 0.35
