"""Subsystem lifecycle and health monitoring manager."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Protocol, cast, runtime_checkable

from osint_nexus.utils.security import SecurityUtility

logger = logging.getLogger("osint_nexus.hierarchy")


@runtime_checkable
class HealthCheckable(Protocol):
    async def health_check(self) -> bool:
        """Perform a health check."""


class SubsystemStatus:
    def __init__(self, subsystem: Any) -> None:
        self.subsystem = subsystem
        self.healthy: bool = True
        self.failure_count: int = 0
        self.last_error: str | None = None
        self.circuit_open: bool = False
        self.recovery_ticks: int = 0  # Used to back-off checks when circuit is open


class HierarchyManager:
    def __init__(
        self,
        check_interval: float = 30.0,
        check_timeout: float = 10.0,  # FIX #2: Added explicit timeout for health checks
        failure_threshold: int = 3,
        abort_event: asyncio.Event | None = None,
    ) -> None:
        self._subsystems: dict[str, SubsystemStatus] = {}
        self._check_interval = check_interval
        self._check_timeout = check_timeout
        self._failure_threshold = failure_threshold
        self._monitor_task: asyncio.Task[None] | None = None
        self._abort_event = abort_event or asyncio.Event()
        self._running = False

    def register(self, name: str, subsystem: Any) -> None:
        if name in self._subsystems:
            logger.warning(
                "Subsystem '%s' already registered. Replacing.", SecurityUtility.sanitize_for_log(name)
            )
        self._subsystems[name] = SubsystemStatus(subsystem)
        logger.info("Subsystem '%s' registered.", SecurityUtility.sanitize_for_log(name))

    async def unregister(self, name: str) -> None:
        """Unregisters and safely shuts down a subsystem. (Now async)"""
        status = self._subsystems.pop(name, None)
        if status:
            await self._shutdown_one(name, status.subsystem)
            logger.info("Subsystem '%s' unregistered.", SecurityUtility.sanitize_for_log(name))

    def get_status(self, name: str) -> SubsystemStatus | None:
        return self._subsystems.get(name)

    def list_subsystems(self) -> dict[str, bool]:
        return {name: status.healthy for name, status in self._subsystems.items()}

    # FIX #5: Added manual reporting for non-HealthCheckable subsystems
    def report_failure(self, name: str, error: str = "Manual failure report") -> None:
        """Manually flag a subsystem as failing (useful for non-checkable modules)."""
        status = self._subsystems.get(name)
        if status:
            status.failure_count += 1
            status.healthy = False
            status.last_error = error
            if status.failure_count >= self._failure_threshold and not status.circuit_open:
                status.circuit_open = True
                logger.warning("Circuit opened for '%s' via manual report.", name)

    def report_success(self, name: str) -> None:
        """Manually flag a subsystem as recovered."""
        status = self._subsystems.get(name)
        if status:
            status.failure_count = 0
            status.healthy = True
            if status.circuit_open:
                status.circuit_open = False
                status.recovery_ticks = 0
                logger.info("Circuit closed for '%s' via manual report.", name)

    async def check_health(self, name: str) -> bool:
        status = self._subsystems.get(name)
        if not status:
            logger.error("Health check on unknown subsystem '%s'.", name)
            return False
        return await self._check_one(name, status)

    async def check_all(self) -> dict[str, bool]:
        results = {}
        # FIX #3: Snapshot keys to prevent dictionary mutation race conditions
        names_to_check = list(self._subsystems.keys())
        checks = [self._check_safe(name) for name in names_to_check]

        if checks:
            done = await asyncio.gather(*checks, return_exceptions=True)
            for name, healthy in zip(names_to_check, done, strict=True):
                if isinstance(healthy, Exception):
                    logger.error("Health check for '%s' raised: %s", name, healthy)
                    results[name] = False
                else:
                    results[name] = cast(bool, healthy)
        return results

    async def start_monitoring(self) -> None:
        if self._running:
            logger.warning("Monitoring already running.")
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Background health monitoring started (interval %.1fs).", self._check_interval)

    async def stop_monitoring(self) -> None:
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
            self._monitor_task = None
        logger.info("Health monitoring stopped.")

    async def _check_one(self, name: str, status: SubsystemStatus) -> bool:
        if self._is_circuit_open(status):
            return False

        healthy = await self._perform_health_check(name, status)

        if healthy:
            self._handle_success(name, status)
        else:
            self._handle_failure(name, status)

        return healthy

    def _is_circuit_open(self, status: SubsystemStatus) -> bool:
        """Checks if the circuit breaker is open and handles recovery backoff."""
        if not status.circuit_open:
            return False

        status.recovery_ticks += 1
        if status.recovery_ticks < 5:
            return True  # Still open, don't hammer the subsystem

        status.recovery_ticks = 0  # Time to probe it again
        return False

    async def _perform_health_check(self, name: str, status: SubsystemStatus) -> bool:
        """Executes the health check for a subsystem."""
        subsystem = status.subsystem
        try:
            if isinstance(subsystem, HealthCheckable):
                return await asyncio.wait_for(subsystem.health_check(), timeout=self._check_timeout)

            # Fallback logic for non-checkable modules
            return status.failure_count < self._failure_threshold
        except TimeoutError:
            logger.error("Health check timed out for '%s' after %.1fs", name, self._check_timeout)
            status.last_error = "Health check timed out"
            return False
        except Exception as exc:
            logger.error("Health check exception for '%s': %s", name, exc)
            status.last_error = str(exc)
            return False

    def _handle_success(self, name: str, status: SubsystemStatus) -> None:
        """Handles a successful health check."""
        status.failure_count = 0
        status.healthy = True
        if status.circuit_open:
            logger.info("Circuit closed for '%s' – subsystem recovered.", name)
            status.circuit_open = False

    def _handle_failure(self, name: str, status: SubsystemStatus) -> None:
        """Handles a failed health check."""
        status.failure_count += 1
        status.healthy = False
        if status.failure_count >= self._failure_threshold and not status.circuit_open:
            status.circuit_open = True
            logger.warning("Circuit opened for '%s' after %d failures.", name, status.failure_count)

    async def _check_safe(self, name: str) -> bool:
        status = self._subsystems.get(name)
        if not status:
            return False
        return await self._check_one(name, status)

    async def _monitor_loop(self) -> None:
        while self._running and not self._abort_event.is_set():
            await self.check_all()
            try:
                await asyncio.wait_for(self._abort_event.wait(), timeout=self._check_interval)
                break
            except TimeoutError:
                continue
        self._running = False

    async def _shutdown_one(self, name: str, subsystem: Any) -> None:
        try:
            if hasattr(subsystem, "shutdown"):
                result = subsystem.shutdown()
                # FIX #4: Actually await async shutdown coroutines to prevent memory leaks
                if asyncio.iscoroutine(result):
                    await result
        except Exception as exc:
            logger.error("Error shutting down '%s': %s", name, exc)

    async def shutdown_all(self) -> None:
        logger.info("Shutting down all subsystems...")
        await self.stop_monitoring()

        # Execute all shutdowns concurrently and safely
        shutdown_tasks = [
            self._shutdown_one(name, status.subsystem) for name, status in self._subsystems.items()
        ]

        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        self._subsystems.clear()
        logger.info("All subsystems shut down.")

    # Backward-compatible deprecated aliases
    def monitor_health(self) -> None:
        logger.warning("monitor_health() is deprecated. Use check_all() or start_monitoring().")
        asyncio.create_task(self.check_all())

    def annihilate(self, name: str) -> None:
        logger.warning("annihilate() is deprecated. Use await unregister().")
        asyncio.create_task(self.unregister(name))
