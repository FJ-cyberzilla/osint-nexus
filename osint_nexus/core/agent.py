"""
Main OSINT agent orchestration module.

Provides an adaptive agent for verifying usernames across multiple platforms
with evasion, validation, and confidence scoring.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, cast

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.confidence import ConfidenceEngine
from osint_nexus.core.config import Config
from osint_nexus.core.correlation import CorrelationEngine
from osint_nexus.core.database import DatabaseManager
from osint_nexus.core.detection import DetectionEngine
from osint_nexus.core.device_inference import DeviceInferenceService
from osint_nexus.core.diff import DiffEngine
from osint_nexus.core.dork import DorkEngine
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.extractor import PivotExtractor
from osint_nexus.core.fingerprint import FingerprintAgent
from osint_nexus.core.health import HealthTracker
from osint_nexus.core.hierarchy import HierarchyManager
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.core.orchestrator import OrchestratorDeps, ProviderProtocol, ScanOrchestrator
from osint_nexus.core.report import AdvancedReportGenerator
from osint_nexus.core.validator import ResultValidator
from osint_nexus.providers.registry import ProviderRegistry
from osint_nexus.utils.helpers import setup_logger
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger(__name__)


@dataclass
class AgentSubsystems:
    """Container for all OSINTAgent sub-systems with strong typing."""

    evasion: EvasionAgent
    network: NetworkManager
    db: DatabaseManager
    registry: ProviderRegistry
    validator: ResultValidator
    confidence: ConfidenceEngine
    dork: DorkEngine
    hierarchy: HierarchyManager
    mimicry: HumanMimicryEngine
    fingerprint: FingerprintAgent
    health: HealthTracker
    report: AdvancedReportGenerator
    detection: DetectionEngine
    orchestrator: ScanOrchestrator
    device_inference: DeviceInferenceService
    correlation: CorrelationEngine
    diff: DiffEngine
    browser_pool: BrowserPoolManager


class OSINTAgent:
    """
    Adaptive OSINT agent for verifying username presence across platforms.

    Features:
    - Concurrent scanning with configurable parallelism
    - Platform health tracking with decay
    - Streaming results via async generator
    - Cancellation and timeout support
    - Integrated evasion, fingerprinting, and confidence scoring
    """

    def __init__(self, username: str, max_concurrency: int = 5):
        from osint_nexus.providers.registry import ProviderRegistry

        self.config = Config()
        self.logger = setup_logger()
        self.username = username
        self.max_concurrency = max_concurrency

        # Build subsystems with shared network manager
        evasion = EvasionAgent(self.config)
        mimicry = HumanMimicryEngine(self.config)
        browser_pool = BrowserPoolManager()
        network = NetworkManager(self.config, evasion, mimicry, browser_pool)
        db_manager = DatabaseManager()
        extractor = PivotExtractor()
        correlation = CorrelationEngine()
        diff = DiffEngine(db_manager)
        fingerprint = FingerprintAgent()
        confidence = ConfidenceEngine()
        dork = DorkEngine(templates=self.config.dork_templates)
        validator = ResultValidator(username)
        health = HealthTracker()
        device_inference = DeviceInferenceService()
        detection = DetectionEngine(weights=self.config.evasion_weights)

        self.subsystems = AgentSubsystems(
            evasion=evasion,
            network=network,
            db=db_manager,
            registry=ProviderRegistry(evasion, network, dork),
            validator=validator,
            confidence=confidence,
            dork=dork,
            hierarchy=HierarchyManager(),
            mimicry=mimicry,
            fingerprint=fingerprint,
            health=health,
            report=AdvancedReportGenerator(),
            detection=detection,
            orchestrator=ScanOrchestrator(
                OrchestratorDeps(health, validator, db_manager, network, mimicry, extractor),
                detection_engine=detection,
                max_concurrency=max_concurrency,
                device_inference=device_inference,
            ),
            device_inference=device_inference,
            correlation=correlation,
            diff=diff,
            browser_pool=browser_pool,
        )

        # Register core subsystems for hierarchy monitoring
        self.subsystems.hierarchy.register("evasion", self.subsystems.evasion)
        self.subsystems.hierarchy.register("network", self.subsystems.network)
        self.subsystems.hierarchy.register("fingerprint", self.subsystems.fingerprint)

        # Scan state
        self.found_platforms: list[str] = []
        self.device_inference_profile: Any | None = None

        # Ensure database is initialized
        import asyncio

        asyncio.create_task(db_manager.ensure_initialized())

    def abort_scan(self) -> None:
        """Signal the running scan to cancel gracefully."""
        self.subsystems.orchestrator.abort()

    async def run_scan(self, username: str, timeout: float | None = None) -> AsyncGenerator[Any]:
        """
        Execute username check across all registered providers concurrently.

        Yields:
            IntelligenceObject instances.
        """
        self.logger.info("Agent starting scan for: %s", username)
        providers = self.subsystems.registry.get_providers()

        async for intel in self.subsystems.orchestrator.run_scan(
            username, cast(list[ProviderProtocol], providers), timeout
        ):
            if intel.found:
                self.found_platforms.append(intel.platform)
                # Capture device inference from the first found platform with data
                if not self.device_inference_profile and "device_inference" in intel.metadata:
                    self.device_inference_profile = intel.metadata["device_inference"]
            yield intel

    def reset_health(self, provider_name: str | None = None) -> None:
        """Reset failure counters for one or all providers."""
        self.subsystems.health.reset(provider_name)

    def get_final_report(self) -> str:
        """Generate a summary report after scan completion."""
        # Using a dummy payload for the example; this should be updated with actual telemetry
        self.subsystems.report.render_hardware_intelligence(
            self.username,
            {
                "is_poisoned": False,
                "shannon_entropy": 3.0,
                "render_time_ms": 1.5,
                "reported_user_agent": "Mozilla/5.0",
            },
        )
        return "Report rendered to console."
