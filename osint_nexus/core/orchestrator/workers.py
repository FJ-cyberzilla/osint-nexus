from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any

from osint_nexus.core.exceptions import ProviderError
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.providers.base import BaseProvider

if TYPE_CHECKING:
    from osint_nexus.core.provider_runner import ProviderRunner

    from .core import OrchestratorDeps

logger = logging.getLogger("osint_nexus.orchestrator.workers")


class ProviderWorker:
    def __init__(self, deps: OrchestratorDeps, provider_runner: ProviderRunner) -> None:
        self.deps = deps
        self.provider_runner = provider_runner

    async def execute(
        self, provider: BaseProvider, username: str, abort_event: asyncio.Event, **microlink_options: Any
    ) -> IntelligenceObject:
        """
        Executes provider logic with injected tools.
        """
        if abort_event.is_set():
            return self._build_error_intel(provider.name, username, "Scan aborted")

        # Circuit breaker check
        if not getattr(self.deps.health, "is_healthy", lambda _: True)(provider.name):
            return self._build_error_intel(provider.name, username, "Skipped (Circuit Breaker Tripped)")

        try:
            intel = await self.provider_runner.run(provider, username, **microlink_options)
            getattr(self.deps.health, "record_success", lambda _: None)(provider.name)
            return intel
        except Exception as exc:
            if os.getenv("DEBUG_PROVIDERS"):
                raise
            logger.error("Scan failure in %s: %s", provider.name, exc, exc_info=True)
            getattr(self.deps.health, "record_failure", lambda _: None)(provider.name)
            return self._build_error_intel(
                provider.name, username, f"{ProviderError.__name__}: {type(exc).__name__}"
            )

    async def semaphored_execute(
        self,
        provider: BaseProvider,
        username: str,
        semaphore: asyncio.Semaphore,
        abort_event: asyncio.Event,
        timeout: float | None = None,
        **microlink_options: Any,
    ) -> IntelligenceObject:
        """
        Wraps execution in semaphore and timeout.
        """
        async with semaphore:
            try:
                if timeout:
                    return await asyncio.wait_for(
                        self.execute(provider, username, abort_event, **microlink_options), timeout=timeout
                    )
                return await self.execute(provider, username, abort_event, **microlink_options)
            except TimeoutError:
                return self._build_error_intel(provider.name, username, "Timeout")

    def build_success_intel(
        self,
        provider: BaseProvider,
        username: str,
        final_found: bool,
        dork: str,
        content: str | None,
        metadata: dict[str, str | int | float | bool],
    ) -> IntelligenceObject:
        """Constructs an IntelligenceObject for a successful scan."""
        return IntelligenceObject(
            platform=provider.name,
            username=username,
            found=final_found,
            dork=dork,
            confidence=1.0 if final_found else 0.0,
            metadata=metadata,
            raw_data=content if final_found else None,
        )

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
