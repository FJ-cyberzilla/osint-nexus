"""Subsystem lifecycle and health monitoring manager."""

from __future__ import annotations

import asyncio
import contextlib
import enum
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, cast, runtime_checkable

from osint_nexus.utils.security import SecurityUtility

logger = logging.getLogger("osint_nexus.hierarchy")


@runtime_checkable
class HealthCheckable(Protocol):
    """Protocol for components supporting explicit health checks."""

    async def health_check(self) -> bool:
        """Perform a health check. Returns True if healthy, False otherwise."""
        ...


class CircuitState(enum.Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, requests blocked
    HALF_OPEN = "HALF_OPEN"  # Probing recovery


@dataclass
class SubsystemStatus:
    subsystem: Any
    healthy: bool = True
    failure_count: int = 0
    last_error: str | None = None
    state: CircuitState = CircuitState.CLOSED
    last_state_change: float = field(default_factory=time.monotonic)
    next_allowed_check: float = 0.0
    current_backoff: float = 5.0  # Initial recovery delay in seconds


class HierarchyManager:
    """Manages subsystem lifecycles, circuit breakers, and async health checks."""

    def __init__(
        self,
        check_interval: float = 30.0,
        check_timeout: float = 10.0,
        failure_threshold: int = 3,
        initial_backoff: float = 5.0,
        max_backoff: float = 300.0,
        backoff_factor: float = 2.0,
        abort_event: asyncio.Event | None = None,
    ) -> None:
        self._subsystems: dict[str, SubsystemStatus] = {}
        self._check_interval = check_interval
        self._check_timeout = check_timeout
        self._failure_threshold = failure_threshold
        self._initial_backoff = initial_backoff
        self._max_backoff = max_backoff
        self._backoff_factor = backoff_factor

        self._monitor_task: asyncio.Task[None] | None = None
        self._abort_event = abort_event or asyncio.Event()
        self._running = False
        self._lock = asyncio.Lock()

    def register(self, name: str, subsystem: Any) -> None:
        """Register a subsystem for monitoring."""
        if name in self._subsystems:
            logger.warning(
                "Subsystem '%s' already registered. Replacing.", SecurityUtility.sanitize_for_log(name)
            )
        self._subsystems[name] = SubsystemStatus(subsystem=subsystem, current_backoff=self._initial_backoff)
        logger.info("Subsystem '%s' registered.", SecurityUtility.sanitize_for_log(name))

    async def unregister(self, name: str) -> None:
        """Unregister and safely shut down a specific subsystem."""
        async with self._lock:
            status = self._subsystems.pop(name, None)

        if status:
            await self._shutdown_one(name, status.subsystem)
            logger.info("Subsystem '%s' unregistered.", SecurityUtility.sanitize_for_log(name))

    def get_status(self, name: str) -> SubsystemStatus | None:
        """Return the current status object for a subsystem."""
        return self._subsystems.get(name)

    def list_subsystems(self) -> dict[str, bool]:
        """Return health mapping for all managed subsystems."""
        return {name: status.healthy for name, status in self._subsystems.items()}

    def report_failure(self, name: str, error: str = "Manual failure report") -> None:
        """Manually flag a subsystem as failing (triggers circuit breaker check)."""
        status = self._subsystems.get(name)
        if not status:
            return

        status.last_error = error
        self._handle_failure(name, status)

    def report_success(self, name: str) -> None:
        """Manually flag a subsystem as recovered (closes circuit breaker)."""
        status = self._subsystems.get(name)
        if not status:
            return

        self._handle_success(name, status)

    async def check_health(self, name: str) -> bool:
        """Check the health of a single subsystem by name."""
        status = self._subsystems.get(name)
        if not status:
            logger.error("Health check on unknown subsystem '%s'.", name)
            return False
        return await self._check_one(name, status)

    async def check_all(self) -> dict[str, bool]:
        """Check health across all registered subsystems concurrently."""
        async with self._lock:
            names_to_check = list(self._subsystems.keys())

        if not names_to_check:
            return {}

        results = await asyncio.gather(
            *(self._check_safe(name) for name in names_to_check), return_exceptions=True
        )

        output: dict[str, bool] = {}
        for name, result in zip(names_to_check, results, strict=True):
            if isinstance(result, Exception):
                logger.error("Health check execution for '%s' failed: %s", name, result)
                output[name] = False
            else:
                output[name] = cast(bool, result)
        return output

    async def start_monitoring(self) -> None:
        """Start background health monitoring loop."""
        if self._running:
            logger.warning("Monitoring loop already active.")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="hierarchy_monitor_loop")
        logger.info(
            "Background health monitoring started (interval: %.1fs, timeout: %.1fs).",
            self._check_interval,
            self._check_timeout,
        )

    async def stop_monitoring(self) -> None:
        """Stop background health monitoring loop cleanly."""
        if not self._running:
            return

        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
            self._monitor_task = None
        logger.info("Health monitoring stopped.")

    async def _check_safe(self, name: str) -> bool:
        status = self._subsystems.get(name)
        if not status:
            return False
        return await self._check_one(name, status)

    async def _check_one(self, name: str, status: SubsystemStatus) -> bool:
        now = time.monotonic()

        # State 1: OPEN Circuit - Check if cooldown backoff window has passed
        if status.state == CircuitState.OPEN:
            if now < status.next_allowed_check:
                return False  # Block check, still backing off

            # Cooldown passed -> transition to HALF_OPEN to probe subsystem
            status.state = CircuitState.HALF_OPEN
            status.last_state_change = now
            logger.info("Circuit for '%s' transitioned to HALF_OPEN. Probing...", name)

        # State 2: Execute check (CLOSED or HALF_OPEN)
        healthy = await self._perform_health_check(name, status)

        if healthy:
            self._handle_success(name, status)
        else:
            self._handle_failure(name, status)

        return healthy

    async def _perform_health_check(self, name: str, status: SubsystemStatus) -> bool:
        subsystem = status.subsystem
        try:
            if isinstance(subsystem, HealthCheckable):
                return await asyncio.wait_for(subsystem.health_check(), timeout=self._check_timeout)

            # Callable fallback check (e.g., sync or async function)
            if callable(subsystem):
                res = subsystem()
                if asyncio.iscoroutine(res) or isinstance(res, Awaitable):
                    res = await asyncio.wait_for(res, timeout=self._check_timeout)
                return bool(res)

            # Fallback for passive components: rely on failure thresholds
            return status.failure_count < self._failure_threshold

        except TimeoutError:
            logger.error("Health check timed out for '%s' after %.1fs", name, self._check_timeout)
            status.last_error = f"Timed out after {self._check_timeout}s"
            return False
        except Exception as exc:
            # Explicitly propagate cancellation
            if isinstance(exc, asyncio.CancelledError):
                raise
            logger.error("Health check exception for '%s': %s", name, exc)
            status.last_error = str(exc)
            return False

    def _handle_success(self, name: str, status: SubsystemStatus) -> None:
        """Handle a healthy check response."""
        status.failure_count = 0
        status.healthy = True
        status.last_error = None

        if status.state != CircuitState.CLOSED:
            logger.info("Circuit closed for '%s' – subsystem fully recovered.", name)
            status.state = CircuitState.CLOSED
            status.last_state_change = time.monotonic()
            status.current_backoff = self._initial_backoff

    def _handle_failure(self, name: str, status: SubsystemStatus) -> None:
        """Handle an unhealthy check response with exponential backoff calculation."""
        status.failure_count += 1
        status.healthy = False
        now = time.monotonic()

        if status.state == CircuitState.HALF_OPEN:
            # Probe failed immediately -> reopening circuit and increasing backoff
            status.current_backoff = min(status.current_backoff * self._backoff_factor, self._max_backoff)
            status.next_allowed_check = now + status.current_backoff
            status.state = CircuitState.OPEN
            status.last_state_change = now
            logger.warning(
                "Circuit reopened for '%s' after failed probe. Next retry in %.1fs.",
                name,
                status.current_backoff,
            )
        elif status.failure_count >= self._failure_threshold and status.state == CircuitState.CLOSED:
            # Threshold reached -> Trip circuit OPEN
            status.state = CircuitState.OPEN
            status.last_state_change = now
            status.next_allowed_check = now + status.current_backoff
            logger.warning(
                "Circuit opened for '%s' after %d failures. Next retry in %.1fs.",
                name,
                status.failure_count,
                status.current_backoff,
            )

    async def _monitor_loop(self) -> None:
        """Continuous background execution loop."""
        while self._running and not self._abort_event.is_set():
            try:
                await self.check_all()
                await asyncio.wait_for(self._abort_event.wait(), timeout=self._check_interval)
                break  # Abort event set
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.critical("Unexpected error in monitoring loop: %s", exc, exc_info=True)
                await asyncio.sleep(1.0)

        self._running = False

    async def _shutdown_one(self, name: str, subsystem: Any) -> None:
        """Shut down a single subsystem cleanly."""
        try:
            shutdown_func: Callable[[], Any] | None = None
            if hasattr(subsystem, "shutdown") and callable(subsystem.shutdown):
                shutdown_func = subsystem.shutdown
            elif hasattr(subsystem, "close") and callable(subsystem.close):
                shutdown_func = subsystem.close

            if shutdown_func:
                result = shutdown_func()
                if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
                    await asyncio.wait_for(result, timeout=self._check_timeout)

        except TimeoutError:
            logger.error("Shutdown timed out for '%s' after %.1fs", name, self._check_timeout)
        except Exception as exc:
            if isinstance(exc, asyncio.CancelledError):
                raise
            logger.error("Error shutting down '%s': %s", name, exc)

    async def shutdown_all(self) -> None:
        """Halt monitoring and cleanly shut down all managed subsystems concurrently."""
        logger.info("Shutting down all subsystems...")
        await self.stop_monitoring()

        async with self._lock:
            subsystems_to_close = list(self._subsystems.items())
            self._subsystems.clear()

        if subsystems_to_close:
            shutdown_tasks = [
                self._shutdown_one(name, status.subsystem) for name, status in subsystems_to_close
            ]
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        logger.info("All subsystems shut down completely.")
