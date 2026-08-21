"""
Facade for the OSINT Nexus framework.

Orchestrates the scan lifecycle across providers, browser management,
and reporting.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from rich.panel import Panel

from osint_nexus.core.browser import BrowserPoolManager
from osint_nexus.core.config import Config
from osint_nexus.core.database import DatabaseManager
from osint_nexus.core.detection import DetectionEngine
from osint_nexus.core.device_inference import DeviceInferenceNetworkEngine
from osint_nexus.core.evasion import EvasionWeights
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.core.extractor import PivotExtractor
from osint_nexus.core.fingerprint import FingerprintAgent
from osint_nexus.core.health import HealthTracker
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.core.orchestrator import OrchestratorDeps, ScanOrchestrator
from osint_nexus.core.report import AdvancedReportGenerator
from osint_nexus.core.validator import ResultValidator
from osint_nexus.providers.registry import ProviderRegistry
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.core.agent")


@dataclass
class AgentSubsystems:
    registry: ProviderRegistry
    orchestrator: ScanOrchestrator
    report: AdvancedReportGenerator
    db: DatabaseManager
    validator: ResultValidator


class OSINTAgent:
    """
    Facade providing a unified interface for the OSINT Nexus scanner.
    """

    def __init__(self, username: str, ja3_hash: str | None = None) -> None:
        """
        Initialize the OSINT Agent for a specific target username.

        Args:
            username: The username to scan.
            ja3_hash: Optional JA3 hash extracted from infrastructure headers.
        """
        self.username = username
        self.config = Config()
        self.evasion_weights = EvasionWeights()
        self.fingerprint_agent = FingerprintAgent(self.config, ja3_hash=ja3_hash)

        # Initialize subsystems
        self.health = HealthTracker()
        self.validator = ResultValidator(username)
        self.db = DatabaseManager(self.config)
        self.mimicry = HumanMimicryEngine(self.config)
        self.extractor = PivotExtractor()

        self.evasion = EvasionAgent(self.config)
        self.browser_pool = BrowserPoolManager()
        self.network = NetworkManager(
            config=self.config,
            evasion=self.evasion,
            mimicry=self.mimicry,
            browser_pool=self.browser_pool,
        )

        self.subsystems = AgentSubsystems(
            registry=ProviderRegistry(
                evasion_manager=self.evasion,
                network_manager=self.network,
            ),
            orchestrator=ScanOrchestrator(
                deps=OrchestratorDeps(
                    health=self.health,
                    validator=self.validator,
                    db_manager=self.db,
                    network=self.network,
                    mimicry=self.mimicry,
                    extractor=self.extractor,
                    fingerprint=self.fingerprint_agent,
                ),
                detection_engine=DetectionEngine(weights=self.evasion_weights),
                device_inference=DeviceInferenceNetworkEngine(),
            ),
            report=AdvancedReportGenerator(self.db),
            db=self.db,
            validator=self.validator,
        )

    @property
    def orchestrator(self) -> ScanOrchestrator:
        """Access the orchestrator subsystem."""
        return self.subsystems.orchestrator

    async def run_scan(self, username: str, timeout: float = 15.0) -> AsyncGenerator[IntelligenceObject]:
        """
        Runs the full scan process for a given username.

        Args:
            username: The username to scan.
            timeout: The maximum time allowed for each provider scan in seconds.

        Yields:
            IntelligenceObject containing scan result metadata.
        """
        await self.db.ensure_initialized()
        providers = self.subsystems.registry.get_providers()
        async for intel in self.subsystems.orchestrator.run_scan(username, providers, timeout=timeout):
            yield intel

    async def get_final_report(self) -> Panel:
        """
        Generates the final report based on gathered intelligence.

        Returns:
            The rich-formatted report object.
        """
        return await self.subsystems.report.generate(self.username)

    def abort_scan(self) -> None:
        """Aborts any currently running scan processes."""
        self.subsystems.orchestrator.abort()
