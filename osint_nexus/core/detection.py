"""DetectionEngine: aggregates novel + signature-based adversarial detection."""

import asyncio
import logging
import re
from typing import TYPE_CHECKING, cast

from osint_nexus.core.detectors.base import BaseDetector
from osint_nexus.core.evasion import EvasionWeights
from osint_nexus.core.report import TelemetryPayload
from osint_nexus.core.type_defs import MetadataDict

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DetectionResult:
    """Structured output from detection analysis."""

    def __init__(
        self,
        evasion_score: float,
        is_automated: bool,
        detector_details: dict[str, float],
    ) -> None:
        self.evasion_score = evasion_score
        self.is_automated = is_automated
        self.detector_details = detector_details


class DetectionEngine:
    """Runs all detectors against telemetry and produces a unified score."""

    def __init__(
        self,
        weights: EvasionWeights,
        detectors: list[BaseDetector] | None = None,
    ) -> None:
        """
        Initializes the DetectionEngine.

        Args:
            weights: Evasion weights configuration.
            detectors: Optional list of novel detectors to run.
        """
        self.weights = weights
        self.detectors = detectors or []

    async def analyze(self, payload: TelemetryPayload, platforms: list[str]) -> DetectionResult:
        """
        Runs signature checks and novel detectors concurrently.

        Args:
            payload: Telemetry data from the scan.
            platforms: List of platforms found.

        Returns:
            A DetectionResult object with the evasion score and details.
        """
        score = 0.0
        details: dict[str, float] = {}

        # Signature-based (fast, sync)
        score += self._check_signatures(payload, platforms)

        # Novel detectors (concurrent, async)
        if self.detectors and payload.raw_metadata:
            score += await self._run_novel_detectors(payload, details)

        final_score = min(score, 1.0)
        return DetectionResult(
            evasion_score=final_score,
            is_automated=final_score > 0.7,
            detector_details=details,
        )

    async def _run_novel_detectors(self, payload: TelemetryPayload, details: dict[str, float]) -> float:
        """
        Runs novel detectors and updates score and details.

        Args:
            payload: Telemetry data.
            details: Dictionary to update with detector scores.

        Returns:
            The total score contribution from novel detectors.
        """
        score = 0.0
        tasks = [d.analyze(cast(MetadataDict, payload.raw_metadata)) for d in self.detectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            name = self.detectors[i].name
            if isinstance(result, Exception):
                logger.warning("Detector %s failed: %s", name, result)
                details[name] = 0.5  # Neutral on failure
                continue
            details[name] = cast(float, result)
            # Invert: detector returns 1.0 for real hardware
            score += (1.0 - cast(float, result)) * self.weights.novel_detector_weight
        return score

    def _check_signatures(self, payload: TelemetryPayload, platforms: list[str]) -> float:
        """
        Performs fast, signature-based checks.

        Args:
            payload: Telemetry data.
            platforms: List of platforms found.

        Returns:
            The total score contribution from signatures.
        """
        score = 0.0

        score += self._check_browser_signatures(payload)

        if len(platforms) > self.weights.platform_density_threshold:
            score += self.weights.platform_density_penalty
        if payload.pipeline_status != "ok":
            score += self.weights.degraded_pipeline_penalty

        return score

    def _check_browser_signatures(self, payload: TelemetryPayload) -> float:
        """
        Checks browser-related signatures from telemetry.

        Args:
            payload: Telemetry data.

        Returns:
            The total score contribution from browser signatures.
        """
        if not payload.browser:
            return 0.0

        browser = payload.browser

        score = 0.0
        checks = [
            (self._has_ai_user_agent(browser.user_agent), self.weights.ai_signature),
            (browser.headless, self.weights.headless_mode),
            (browser.webdriver, self.weights.webdriver_active),
            (browser.automation_plugins, self.weights.automation_plugins),
        ]

        for condition, weight in checks:
            if condition:
                score += weight
        return score

    def _has_ai_user_agent(self, ua: str) -> bool:
        """
        Checks against AI footprint regex.

        Args:
            ua: User agent string.

        Returns:
            True if AI footprint is detected.
        """
        pattern = re.compile(
            r"(openai|gptbot|claude|anthropic|cohere|"
            r"gemini|perplex|bytespider|ccbot|crawler)",
            re.IGNORECASE,
        )
        return bool(pattern.search(ua))
