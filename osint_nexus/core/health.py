"""
Manages provider health tracking to avoid hammering failing platforms.
"""
from typing import Dict, Optional

class HealthTracker:
    def __init__(self) -> None:
        self.platform_health: Dict[str, int] = {}

    def is_healthy(self, provider_name: str) -> bool:
        return self.platform_health.get(provider_name, 0) < 3

    def record_failure(self, provider_name: str) -> None:
        self.platform_health[provider_name] = (
            self.platform_health.get(provider_name, 0) + 1
        )

    def record_success(self, provider_name: str) -> None:
        if self.platform_health.get(provider_name, 0) > 0:
            self.platform_health[provider_name] -= 1

    def reset(self, provider_name: Optional[str] = None) -> None:
        if provider_name:
            self.platform_health.pop(provider_name, None)
        else:
            self.platform_health.clear()
