"""
Manages provider health tracking to avoid hammering failing platforms.
"""

import logging
import time

logger = logging.getLogger(__name__)


class HealthTracker:
    def __init__(self, failure_threshold: int = 5, default_recovery_timeout: float = 60.0) -> None:
        self.platform_failures: dict[str, int] = {}
        self.last_failure_times: dict[str, float] = {}
        self.provider_timeouts: dict[str, float] = {}
        self.failure_threshold = failure_threshold
        self.default_recovery_timeout = default_recovery_timeout

    def set_provider_timeout(self, provider_name: str, timeout: float) -> None:
        """Sets a specific recovery timeout for a provider."""
        self.provider_timeouts[provider_name] = timeout

    def is_healthy(self, provider_name: str) -> bool:
        # If failed, check if it's time to attempt recovery
        if self.platform_failures.get(provider_name, 0) >= self.failure_threshold:
            return self.should_attempt_recovery(provider_name)
        return True

    def should_attempt_recovery(self, provider_name: str) -> bool:
        """Returns True if the provider is failed but past the configured recovery timeout."""
        last_fail = self.last_failure_times.get(provider_name, 0.0)
        timeout = self.provider_timeouts.get(provider_name, self.default_recovery_timeout)
        return (time.time() - last_fail) > timeout

    def is_degraded(self, provider_name: str) -> bool:
        """Returns True if the provider is nearing the failure threshold."""
        failures = self.platform_failures.get(provider_name, 0)
        return (self.failure_threshold / 2) <= failures < self.failure_threshold

    def record_failure(self, provider_name: str) -> None:
        count = self.platform_failures.get(provider_name, 0) + 1
        self.platform_failures[provider_name] = count
        self.last_failure_times[provider_name] = time.time()

        if count >= self.failure_threshold:
            logger.error("Provider %s is now marked as FAILED (failures: %d)", provider_name, count)
        elif self.is_degraded(provider_name):
            logger.warning("Provider %s is DEGRADED (failures: %d)", provider_name, count)

    def record_success(self, provider_name: str) -> None:
        # On success, clear failure state
        self.platform_failures[provider_name] = 0
        self.last_failure_times.pop(provider_name, None)

    def reset(self, provider_name: str | None = None) -> None:
        if provider_name:
            self.platform_failures.pop(provider_name, None)
            self.last_failure_times.pop(provider_name, None)
            self.provider_timeouts.pop(provider_name, None)
        else:
            self.platform_failures.clear()
            self.last_failure_times.clear()
            self.provider_timeouts.clear()
