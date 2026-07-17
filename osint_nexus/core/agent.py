"""
Main OSINT agent orchestration module.

Provides an adaptive agent for verifying usernames across multiple platforms
with evasion, validation, and confidence scoring.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncGenerator

from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.database import DatabaseManager
from osint_nexus.core.validator import ResultValidator
from osint_nexus.core.config import Config
from osint_nexus.core.confidence import ConfidenceEngine
from osint_nexus.core.hierarchy import HierarchyManager
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.core.fingerprint import FingerprintAgent
from osint_nexus.core.health import HealthTracker
from osint_nexus.core.report import ReportGenerator
from osint_nexus.core.orchestrator import ScanOrchestrator, OrchestratorDeps
from osint_nexus.core.device_inference import DeviceInferenceService
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
    hierarchy: HierarchyManager
    mimicry: HumanMimicryEngine
    fingerprint: FingerprintAgent
    health: HealthTracker
    report: ReportGenerator
    orchestrator: ScanOrchestrator
    device_inference: DeviceInferenceService


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
        self.config = Config()
        self.logger = setup_logger()
        self.username = username
        self.max_concurrency = max_concurrency

        # Build subsystems with shared network manager
        evasion = EvasionAgent(self.config)
        mimicry = HumanMimicryEngine(self.config)
        network = NetworkManager(self.config, evasion, mimicry)
        db_manager = DatabaseManager()
        fingerprint = FingerprintAgent()
        confidence = ConfidenceEngine()
        validator = ResultValidator(username)
        health = HealthTracker()
        device_inference = DeviceInferenceService()

        self.subsystems = AgentSubsystems(
            evasion=evasion,
            network=network,
            db=db_manager,
            registry=ProviderRegistry(evasion, network),
            validator=validator,
            confidence=confidence,
            hierarchy=HierarchyManager(),
            mimicry=mimicry,
            fingerprint=fingerprint,
            health=health,
            report=ReportGenerator(fingerprint, evasion, confidence),
            orchestrator=ScanOrchestrator(
                OrchestratorDeps(health, validator, db_manager, network, mimicry),
                max_concurrency,
                device_inference
            ),
            device_inference=device_inference
        )

        # Register core subsystems for hierarchy monitoring
        self.subsystems.hierarchy.register("evasion", self.subsystems.evasion)
        self.subsystems.hierarchy.register("network", self.subsystems.network)
        self.subsystems.hierarchy.register("fingerprint", self.subsystems.fingerprint)

        # Scan state
        self.found_platforms: List[str] = []
        self.device_inference_profile: Optional[Any] = None

    def abort_scan(self) -> None:
        """Signal the running scan to cancel gracefully."""
        self.subsystems.orchestrator.abort()

    async def run_scan(
        self, username: str, timeout: Optional[float] = None
    ) -> AsyncGenerator[Any, None]:
        """
        Execute username check across all registered providers concurrently.

        Yields:
            IntelligenceObject instances.
        """
        self.logger.info("Agent starting scan for: %s", username)
        providers = self.subsystems.registry.get_providers()

        async for intel in self.subsystems.orchestrator.run_scan(username, providers, timeout):
            if intel.found:
                self.found_platforms.append(intel.platform)
                # Capture device inference from the first found platform with data
                if not self.device_inference_profile and "device_inference" in intel.metadata:
                    self.device_inference_profile = intel.metadata["device_inference"]
            yield intel

    def reset_health(self, provider_name: Optional[str] = None) -> None:
        """Reset failure counters for one or all providers."""
        self.subsystems.health.reset(provider_name)

    def get_final_report(self) -> str:
        """Generate a summary report after scan completion."""
        return self.subsystems.report.generate_summary(
            self.found_platforms, 
            self.device_inference_profile,
            target=self.username
        )
