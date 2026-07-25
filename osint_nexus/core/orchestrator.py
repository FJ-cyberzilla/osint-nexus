"""
Orchestrates the scan lifecycle across multiple providers.

Production-hardened with bounded concurrency, strict timeouts,
and immutable DTOs, this module integrates network evasion and
behavioral mimicry into the provider execution loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.utils.network import NetworkManager
from osint_nexus.core.detection import DetectionEngine
from osint_nexus.core.report import TelemetryPayload

logger = logging.getLogger("osint_nexus.orchestrator")


@dataclass(frozen=True)
class OrchestratorDeps:
    """Container for core service dependencies to reduce orchestrator bloat."""

    health: Any
    validator: Any
    db_manager: Any
    network: NetworkManager
    mimicry: HumanMimicryEngine


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

    def abort(self) -> None:
        """Signals all active and pending scans to terminate gracefully."""
        logger.warning("Scan abort requested. Cancelling pending operations.")
        self._abort_event.set()

    async def _execute_provider(
        self, provider: ProviderProtocol, username: str, **microlink_options: Any
    ) -> IntelligenceObject:
        """
        Internal worker that executes provider logic with injected tools.
        This handles the full lifecycle of a single provider check.
        """
        if self._abort_event.is_set():
            return self._build_error_intel(provider.name, username, "Scan aborted")

        # Circuit breaker check
        if not getattr(self.deps.health, "is_healthy", lambda _: True)(provider.name):
            return self._build_error_intel(provider.name, username, "Skipped (Circuit Breaker Tripped)")

        try:
            return await self._perform_provider_check(provider, username, microlink_options)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            if os.getenv("DEBUG_PROVIDERS"):
                raise
            logger.error("Scan failure in %s: %s", provider.name, exc, exc_info=True)
            getattr(self.deps.health, "record_failure", lambda _: None)(provider.name)
            return self._build_error_intel(provider.name, username, f"Error: {type(exc).__name__}")

    async def _perform_provider_check(
        self, provider: ProviderProtocol, username: str, microlink_options: dict[str, Any]
    ) -> IntelligenceObject:
        """Executes the provider check logic."""
        raw_found, content = await provider.check_username(
            username, network=self.deps.network, mimicry=self.deps.mimicry, **microlink_options
        )
        dork = provider.get_dork_query(username)

        final_found = raw_found and self.deps.validator.validate(content, provider.name)

        metadata = await self._infer_metadata(provider, username, content, final_found)

        await self.deps.db_manager.save_result(username, provider.name, final_found)

        intel = self._build_success_intel(provider, username, final_found, dork, content, metadata)

        getattr(self.deps.health, "record_success", lambda _: None)(provider.name)
        return intel

    async def _infer_metadata(self, provider: ProviderProtocol, username: str, content: Any, final_found: bool) -> dict[str, Any]:
        """Infers metadata for a provider result."""
        metadata: dict[str, Any] = {}
        if final_found and self.device_inference:
            profile = await self.device_inference.infer(str(content), provider.get_metadata(username))
            metadata["device_inference"] = profile.model_dump(mode="json")
            logger.info("Inferred device for %s: %s", provider.name, metadata["device_inference"])
        return metadata

    def _build_success_intel(
        self, provider: ProviderProtocol, username: str, final_found: bool, dork: str, content: Any, metadata: dict[str, Any]
    ) -> IntelligenceObject:
        """Constructs an IntelligenceObject for a successful scan."""
        return IntelligenceObject(
            platform=provider.name,
            username=username,
            found=final_found,
            dork=dork,
            confidence=1.0 if final_found else 0.0,
            metadata=metadata,
            raw_data=str(content) if final_found else None,
        )

    async def _semaphored_worker(
        self,
        provider: ProviderProtocol,
        username: str,
        semaphore: asyncio.Semaphore,
        timeout: float | None = None,
        **microlink_options: Any,
    ) -> IntelligenceObject:
        """
        Wraps execution in semaphore and timeout.
        Ensures that concurrency limits are respected and hanging tasks are aborted.
        """
        async with semaphore:
            try:
                if timeout:
                    return await asyncio.wait_for(
                        self._execute_provider(provider, username, **microlink_options), timeout=timeout
                    )
                return await self._execute_provider(provider, username, **microlink_options)
            except TimeoutError:
                return self._build_error_intel(provider.name, username, "Timeout")

    async def run_scan(
        self,
        username: str,
        providers: list[ProviderProtocol],
        timeout: float | None = 15.0,
        **microlink_options: Any,
    ) -> AsyncGenerator[IntelligenceObject, None]:
        """
        Executes a bounded scan across providers.

        Yields IntelligenceObject instances as soon as each provider finishes.
        """
        self._abort_event.clear()
        semaphore = asyncio.Semaphore(self.max_concurrency)

        tasks = [
            asyncio.create_task(self._semaphored_worker(p, username, semaphore, timeout, **microlink_options))
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

    async def _process_scan_tasks(self, tasks: list[asyncio.Task]) -> AsyncGenerator[IntelligenceObject, None]:
        """Processes completed scan tasks."""
        for coro in asyncio.as_completed(tasks):
            if self._abort_event.is_set():
                break
            yield await coro

    def _cancel_pending_tasks(self, tasks: list[asyncio.Task]) -> None:
        """Cancels any pending tasks."""
        for task in tasks:
            if not task.done():
                task.cancel()

    async def _run_detection_analysis(self, results: list[IntelligenceObject]) -> None:
        """Runs the detection engine analysis after a scan."""
        telemetry = TelemetryPayload(
            browser=None, # Needs actual browser info
            raw_metadata={},
            pipeline_status="ok"
        )
        platforms = [r.platform for r in results if r.found]
        
        detection_result = await self.detection.analyze(telemetry, platforms)
        logger.info("Detection score: %f", detection_result.evasion_score)

    def _build_error_intel(self, platform: str, username: str, error_msg: str) -> IntelligenceObject:
        """Helper to safely construct an IntelligenceObject representing a failure."""
        return IntelligenceObject(
            platform=platform,
            username=username,
            found=False,
            dork="",
            confidence=0.0,
            metadata={"error": error_msg},
        )
