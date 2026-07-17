"""
Orchestrates the scan lifecycle across multiple providers.

Production-hardened with bounded concurrency, strict timeouts,
and immutable DTOs, this module integrates network evasion and
behavioral mimicry into the provider execution loop.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Protocol, runtime_checkable

from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.utils.network import NetworkManager
from osint_nexus.core.mimicry import HumanMimicryEngine

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
        self,
        username: str,
        network: NetworkManager,
        mimicry: HumanMimicryEngine,
        **kwargs: Any
    ) -> tuple[bool, Any]:
        """Check if username exists on provider."""
        ...

    def get_dork_query(self, username: str) -> str:
        """Get the dork query for this provider."""
        ...

    def get_metadata(self, username: str) -> Dict[str, Any]:
        """Get provider-specific metadata."""
        ...


class ScanOrchestrator:
    """Manages concurrent provider execution and intelligence synthesis."""

    def __init__(
        self,
        deps: OrchestratorDeps,
        max_concurrency: int = 5,
        device_inference: Optional[Any] = None
    ) -> None:
        """Initialize the orchestrator with dependencies and configuration."""
        self.deps = deps
        self.max_concurrency = max(1, max_concurrency)
        self.device_inference = device_inference
        self._abort_event = asyncio.Event()

    def abort(self) -> None:
        """Signals all active and pending scans to terminate gracefully."""
        logger.warning("Scan abort requested. Cancelling pending operations.")
        self._abort_event.set()

    async def run_scan(
        self,
        username: str,
        providers: List[ProviderProtocol],
        timeout: Optional[float] = 15.0,
        **microlink_options: Any
    ) -> AsyncGenerator[IntelligenceObject, None]:
        """
        Executes a bounded scan across providers.

        Yields IntelligenceObject instances as soon as each provider finishes.
        """
        self._abort_event.clear()
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _execute_provider(provider: ProviderProtocol) -> IntelligenceObject:
            """
            Internal worker that executes provider logic with injected tools.
            This handles the full lifecycle of a single provider check.
            """
            if self._abort_event.is_set():
                return self._build_error_intel(provider.name, username, "Scan aborted")

            # Circuit breaker check
            if not getattr(self.deps.health, "is_healthy", lambda _: True)(provider.name):
                return self._build_error_intel(provider.name, username, "Skipped (Unhealthy)")

            try:
                raw_found, content = await provider.check_username(
                    username,
                    network=self.deps.network,
                    mimicry=self.deps.mimicry,
                    **microlink_options
                )
                dork = provider.get_dork_query(username)

                final_found = raw_found and self.deps.validator.validate(content, provider.name)

                metadata: Dict[str, Any] = {}
                if final_found and self.device_inference:
                    profile = self.device_inference.infer(str(content), provider.get_metadata(username))
                    metadata["device_inference"] = profile.model_dump(mode="json")
                    logger.info("Inferred device for %s: %s", provider.name, metadata["device_inference"])

                await self.deps.db_manager.save_result(username, provider.name, final_found)

                intel = IntelligenceObject(
                    platform=provider.name,
                    username=username,
                    found=final_found,
                    dork=dork,
                    confidence=1.0 if final_found else 0.0,
                    metadata=metadata,
                    raw_data=str(content) if final_found else None
                )

                getattr(self.deps.health, "record_success", lambda _: None)(provider.name)
                return intel

            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.error("Scan failure in %s: %s", provider.name, exc, exc_info=True)
                getattr(self.deps.health, "record_failure", lambda _: None)(provider.name)
                return self._build_error_intel(provider.name, username, f"Error: {type(exc).__name__}")

        async def _semaphored_worker(provider: ProviderProtocol) -> IntelligenceObject:
            """
            Wraps execution in semaphore and timeout.
            Ensures that concurrency limits are respected and hanging tasks are aborted.
            """
            async with semaphore:
                try:
                    if timeout:
                        return await asyncio.wait_for(_execute_provider(provider), timeout=timeout)
                    return await _execute_provider(provider)
                except asyncio.TimeoutError:
                    return self._build_error_intel(provider.name, username, "Timeout")

        tasks = [asyncio.create_task(_semaphored_worker(p)) for p in providers]
        try:
            for coro in asyncio.as_completed(tasks):
                if self._abort_event.is_set():
                    break
                yield await coro
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

    def _build_error_intel(self, platform: str, username: str, error_msg: str) -> IntelligenceObject:
        """Helper to safely construct an IntelligenceObject representing a failure."""
        return IntelligenceObject(
            platform=platform,
            username=username,
            found=False,
            dork="",
            confidence=0.0,
            metadata={"error": error_msg}
        )
