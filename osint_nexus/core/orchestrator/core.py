from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from osint_nexus.core.detection import DetectionEngine
from osint_nexus.core.extractor import PivotExtractor
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.core.provider_runner import ProviderRunner
from osint_nexus.core.report import TelemetryPayload
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager

from .workers import ProviderWorker

logger = logging.getLogger("osint_nexus.orchestrator.core")


@dataclass(frozen=True)
class OrchestratorDeps:
    """Container for core service dependencies to reduce orchestrator bloat."""

    health: Any
    validator: Any
    db_manager: Any
    network: NetworkManager
    mimicry: HumanMimicryEngine
    extractor: PivotExtractor


@runtime_checkable
class ProviderProtocol(Protocol):
    """Protocol defining the required interface for all OSINT providers."""

    name: str

    async def check_username(
        self, username: str, network: NetworkManager, mimicry: HumanMimicryEngine, **kwargs: Any
    ) -> tuple[bool, Any]:
        """Check if username exists on provider."""
        ...

    def get_dork_query(self, username: str) -> str:
        """Get the dork query for this provider."""
        ...

    def get_metadata(self, username: str) -> dict[str, Any]:
        """Get provider-specific metadata."""
        ...


class ScanOrchestrator:
    """Manages concurrent provider execution and intelligence synthesis."""

    def __init__(
        self,
        deps: OrchestratorDeps,
        detection_engine: DetectionEngine,
        max_concurrency: int = 5,
        device_inference: Any | None = None,
    ) -> None:
        """Initialize the orchestrator with dependencies and configuration."""
        self.deps = deps
        self.detection = detection_engine
        self.max_concurrency = max(1, max_concurrency)
        self.device_inference = device_inference
        self._abort_event = asyncio.Event()

        self.provider_runner = ProviderRunner(
            validator=self.deps.validator,
            db_manager=self.deps.db_manager,
            network=self.deps.network,
            mimicry=self.deps.mimicry,
            extractor=self.deps.extractor,
            device_inference=device_inference,
        )
        self.worker = ProviderWorker(self.deps, self.provider_runner)

    def abort(self) -> None:
        """Signals all active and pending scans to terminate gracefully."""
        logger.warning("Scan abort requested. Cancelling pending operations.")
        self._abort_event.set()

    async def run_scan(
        self,
        username: str,
        providers: list[BaseProvider],
        timeout: float | None = 15.0,
        **microlink_options: Any,
    ) -> AsyncGenerator[IntelligenceObject]:
        """
        Executes a bounded scan across providers.
        """
        self._abort_event.clear()
        semaphore = asyncio.Semaphore(self.max_concurrency)

        tasks = [
            asyncio.create_task(
                self.worker.semaphored_execute(
                    p, username, semaphore, self._abort_event, timeout, **microlink_options
                )
            )
            for p in providers
        ]

        results: list[IntelligenceObject] = []
        try:
            async for result in self._process_scan_tasks(tasks):
                results.append(result)
                yield result
        finally:
            self._cancel_pending_tasks(tasks)

        await self._run_detection_analysis(results)

    async def _process_scan_tasks(self, tasks: list[asyncio.Task[Any]]) -> AsyncGenerator[IntelligenceObject]:
        """Processes completed scan tasks."""
        for coro in asyncio.as_completed(tasks):
            if self._abort_event.is_set():
                break
            yield await coro

    def _cancel_pending_tasks(self, tasks: list[asyncio.Task[Any]]) -> None:
        """Cancels any pending tasks."""
        for task in tasks:
            if not task.done():
                task.cancel()

    async def _run_detection_analysis(self, results: list[IntelligenceObject]) -> None:
        """Runs the detection engine analysis after a scan."""
        telemetry = TelemetryPayload(
            browser=None,  # Needs actual browser info
            raw_metadata={},
            pipeline_status="ok",
        )
        platforms = [r.platform for r in results if r.found]

        detection_result = await self.detection.analyze(telemetry, platforms)
        logger.info("Detection score: %f", detection_result.evasion_score)
