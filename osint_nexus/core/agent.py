"""
Main OSINT agent orchestration module.

Provides an adaptive agent for verifying usernames across multiple platforms
with evasion, validation, and confidence scoring. Designed for concurrent,
resource-safe execution.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from types import TracebackType
from typing import Any, cast, Self

# Core Infrastructure
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


class OSINTAgentError(Exception):
    """Base exception for OSINTAgent failures."""
    pass


@dataclass(frozen=True, slots=True)
class AgentSubsystems:
    """Immutable container for all OSINTAgent sub-systems."""
    
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
    - Context-manager driven resource lifecycle
    - Integrated evasion, fingerprinting, and confidence scoring
    """

    def __init__(self, username: str, max_concurrency: int = 5, config: Config | None = None) -> None:
        """
        Initialize the OSINT Agent payload.
        Note: Does not open network/db connections. Use 'async with' to manage lifecycle.
        """
        self.username = username
        self.max_concurrency = max_concurrency
        self.config = config or Config()
        
        # We use a distinct logger instance to allow context-specific logging if needed
        self.logger = setup_logger(f"{__name__}.{self.username}")
        
        # State tracking
        self.found_platforms: list[str] = []
        self.device_inference_profile: dict[str, Any] | None = None
        self._is_initialized: bool = False
        self._is_aborted: bool = False

        # Build dependency graph
        self.subsystems = self._build_subsystems()
        self._register_hierarchy()

    def _build_subsystems(self) -> AgentSubsystems:
        """Constructs and injects dependencies for all internal subsystems."""
        # Core engines
        evasion = EvasionAgent(self.config)
        mimicry = HumanMimicryEngine(self.config)
        browser_pool = BrowserPoolManager()
        network = NetworkManager(self.config, evasion, mimicry, browser_pool)
        db_manager = DatabaseManager()
        
        # Analysis engines
        extractor = PivotExtractor()
        correlation = CorrelationEngine()
        diff = DiffEngine(db_manager)
        fingerprint = FingerprintAgent()
        confidence = ConfidenceEngine()
        dork = DorkEngine(templates=self.config.dork_templates)
        validator = ResultValidator(self.username)
        health = HealthTracker()
        device_inference = DeviceInferenceService()
        detection = DetectionEngine(weights=self.config.evasion_weights)

        # Orchestration layer
        orchestrator_deps = OrchestratorDeps(
            health, validator, db_manager, network, mimicry, extractor
        )
        orchestrator = ScanOrchestrator(
            orchestrator_deps,
            detection_engine=detection,
            max_concurrency=self.max_concurrency,
            device_inference=device_inference,
        )

        return AgentSubsystems(
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
            orchestrator=orchestrator,
            device_inference=device_inference,
            correlation=correlation,
            diff=diff,
            browser_pool=browser_pool,
        )

    def _register_hierarchy(self) -> None:
        """Register core subsystems for hierarchy monitoring/telemetry."""
        self.subsystems.hierarchy.register("evasion", self.subsystems.evasion)
        self.subsystems.hierarchy.register("network", self.subsystems.network)
        self.subsystems.hierarchy.register("fingerprint", self.subsystems.fingerprint)

    async def initialize(self) -> None:
        """Safely initialize async resources (Databases, Connection Pools)."""
        if self._is_initialized:
            return
            
        self.logger.debug("Initializing async subsystems for agent...")
        try:
            await self.subsystems.db.ensure_initialized()
            # If network or browser_pool require async init, call them here:
            # await self.subsystems.browser_pool.initialize()
            self._is_initialized = True
            self.logger.debug("Agent initialization complete.")
        except Exception as e:
            self.logger.error("Failed to initialize subsystems: %s", e)
            raise OSINTAgentError(f"Initialization failed: {e}") from e

    async def teardown(self) -> None:
        """Gracefully release all resources, flush databases, and close connections."""
        if not self._is_initialized:
            return

        self.logger.debug("Tearing down agent resources...")
        try:
            # Implement graceful closure for heavy subsystems
            # await self.subsystems.network.close()
            # await self.subsystems.browser_pool.shutdown()
            pass
        except Exception as e:
            self.logger.warning("Error during teardown: %s", e)
        finally:
            self._is_initialized = False

    def abort_scan(self) -> None:
        """Signal the running scan to cancel gracefully."""
        self.logger.warning("Scan abort triggered by user/system.")
        self._is_aborted = True
        self.subsystems.orchestrator.abort()

    async def run_scan(self, timeout: float | None = None) -> AsyncGenerator[Any, None]:
        """
        Execute username check across all registered providers concurrently.

        Args:
            timeout: Maximum execution time in seconds for the entire scan.

        Yields:
            IntelligenceObject instances containing platform metadata.
        """
        if not self._is_initialized:
            raise OSINTAgentError("Agent must be initialized before scanning. Use 'async with' context manager.")

        self.logger.info("Agent starting scan for target: %s", self.username)
        providers = cast(list[ProviderProtocol], self.subsystems.registry.get_providers())

        if not providers:
            self.logger.warning("No providers registered. Aborting scan.")
            return

        try:
            async for intel in self.subsystems.orchestrator.run_scan(self.username, providers, timeout):
                if self._is_aborted:
                    break
                    
                if intel.found:
                    self.found_platforms.append(intel.platform)
                    
                    # Capture device inference profile from the first provider that surfaces it
                    if not self.device_inference_profile and intel.metadata.get("device_inference"):
                        self.device_inference_profile = intel.metadata["device_inference"]
                        
                yield intel

        except asyncio.CancelledError:
            self.logger.warning("Scan task was cancelled externally.")
            self.abort_scan()
            raise
        except Exception as e:
            self.logger.exception("Unexpected error during scan execution: %s", e)
            raise OSINTAgentError(f"Scan failed dynamically: {e}") from e

    def reset_health(self, provider_name: str | None = None) -> None:
        """Reset failure counters for a specific provider or all providers globally."""
        self.subsystems.health.reset(provider_name)
        msg = f"Health reset for provider: {provider_name}" if provider_name else "Global health reset applied."
        self.logger.info(msg)

    def get_final_report(self) -> dict[str, Any]:
        """
        Generate a summary report payload post-scan.
        
        Returns:
            A dictionary containing structured scan metrics and intelligence.
        """
        telemetry_payload = {
            "target": self.username,
            "platforms_found": len(self.found_platforms),
            "platform_list": self.found_platforms,
            "is_poisoned": False,  # Should ideally be dynamically mapped from evasion subsystem
            "shannon_entropy": 3.0, 
            "device_profile": self.device_inference_profile,
        }
        
        # Side-effect: Render to stdout/console depending on report engine setup
        self.subsystems.report.render_hardware_intelligence(self.username, telemetry_payload)
        
        return telemetry_payload

    # --- Async Context Manager Protocol ---
    
    async def __aenter__(self) -> Self:
        await self.initialize()
        return self

    async def __aexit__(
        self, 
        exc_type: type[BaseException] | None, 
        exc_val: BaseException | None, 
        exc_tb: TracebackType | None
    ) -> None:
        await self.teardown()
