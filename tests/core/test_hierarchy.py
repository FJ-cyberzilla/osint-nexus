import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from osint_nexus.hierarchy import CircuitState, HierarchyManager


class DummyHealthCheckable:
    def __init__(self, healthy: bool = True):
        self._healthy = healthy
        self.check_count = 0

    def set_healthy(self, healthy: bool) -> None:
        self._healthy = healthy

    async def health_check(self) -> bool:
        self.check_count += 1
        return self._healthy


@pytest.fixture
def hierarchy():
    """Provides a fresh HierarchyManager configured with fast parameters for testing."""
    return HierarchyManager(
        check_interval=1.0,
        check_timeout=2.0,
        failure_threshold=3,
        initial_backoff=10.0,
        max_backoff=60.0,
        backoff_factor=2.0,
    )


# ---------------------------------------------------------------------------
# State Transition Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_initial_state_is_closed(hierarchy):
    subsystem = DummyHealthCheckable(healthy=True)
    hierarchy.register("test_subsystem", subsystem)

    healthy = await hierarchy.check_health("test_subsystem")

    assert healthy is True
    status = hierarchy.get_status("test_subsystem")
    assert status.state == CircuitState.CLOSED
    assert status.failure_count == 0


@pytest.mark.asyncio
async def test_circuit_trips_open_after_reaching_failure_threshold(hierarchy):
    subsystem = DummyHealthCheckable(healthy=False)
    hierarchy.register("test_subsystem", subsystem)

    # Threshold is 3 failures
    for _ in range(2):
        assert await hierarchy.check_health("test_subsystem") is False
        assert hierarchy.get_status("test_subsystem").state == CircuitState.CLOSED

    # 3rd failure trips the circuit
    assert await hierarchy.check_health("test_subsystem") is False
    status = hierarchy.get_status("test_subsystem")
    assert status.state == CircuitState.OPEN
    assert status.failure_count == 3
    assert status.next_allowed_check > time.monotonic()


@pytest.mark.asyncio
async def test_open_circuit_blocks_checks_during_cooldown(hierarchy):
    subsystem = DummyHealthCheckable(healthy=False)
    hierarchy.register("test_subsystem", subsystem)

    # Trip the circuit OPEN
    for _ in range(3):
        await hierarchy.check_health("test_subsystem")

    initial_check_count = subsystem.check_count

    # Immediate subsequent check should be blocked without executing subsystem.health_check()
    healthy = await hierarchy.check_health("test_subsystem")
    assert healthy is False
    assert subsystem.check_count == initial_check_count  # Call count did not increase


@pytest.mark.asyncio
async def test_circuit_transitions_to_half_open_after_backoff_expires(hierarchy, monkeypatch):
    subsystem = DummyHealthCheckable(healthy=False)
    hierarchy.register("test_subsystem", subsystem)

    # Trip circuit OPEN
    for _ in range(3):
        await hierarchy.check_health("test_subsystem")

    status = hierarchy.get_status("test_subsystem")
    assert status.state == CircuitState.OPEN

    # Fast-forward monotonic time past the backoff window (initial_backoff = 10.0s)
    future_time = time.monotonic() + 15.0
    monkeypatch.setattr(time, "monotonic", lambda: future_time)

    # Now fix the subsystem so the probe will succeed
    subsystem.set_healthy(True)

    # Next check probes in HALF_OPEN and closes the circuit on success
    healthy = await hierarchy.check_health("test_subsystem")
    assert healthy is True
    assert status.state == CircuitState.CLOSED
    assert status.failure_count == 0
    assert status.current_backoff == hierarchy._initial_backoff


@pytest.mark.asyncio
async def test_failed_probe_in_half_open_reopens_circuit_with_exponential_backoff(hierarchy, monkeypatch):
    subsystem = DummyHealthCheckable(healthy=False)
    hierarchy.register("test_subsystem", subsystem)

    # Trip circuit OPEN (backoff initialized to 10.0s)
    for _ in range(3):
        await hierarchy.check_health("test_subsystem")

    status = hierarchy.get_status("test_subsystem")
    initial_backoff = status.current_backoff

    # Fast-forward time past backoff delay
    future_time = time.monotonic() + 15.0
    monkeypatch.setattr(time, "monotonic", lambda: future_time)

    # Probe fails while in HALF_OPEN
    healthy = await hierarchy.check_health("test_subsystem")
    assert healthy is False
    assert status.state == CircuitState.OPEN

    # Exponential backoff applied (10.0 * 2.0 = 20.0s)
    assert status.current_backoff == initial_backoff * hierarchy._backoff_factor
    assert status.next_allowed_check == future_time + status.current_backoff


# ---------------------------------------------------------------------------
# Fallbacks & Manual State Override Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_callable_and_async_callable_fallbacks(hierarchy):
    sync_func = MagicMock(return_value=True)
    async_func = AsyncMock(return_value=True)

    hierarchy.register("sync_subsystem", sync_func)
    hierarchy.register("async_subsystem", async_func)

    assert await hierarchy.check_health("sync_subsystem") is True
    assert await hierarchy.check_health("async_subsystem") is True

    sync_func.assert_called_once()
    async_func.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_report_failure_and_success(hierarchy):
    passive_component = {"name": "legacy_service"}
    hierarchy.register("passive", passive_component)

    # Manually flag failures up to threshold
    hierarchy.report_failure("passive", error="DB connection drop")
    hierarchy.report_failure("passive", error="DB connection drop")
    hierarchy.report_failure("passive", error="DB connection drop")

    status = hierarchy.get_status("passive")
    assert status.state == CircuitState.OPEN
    assert status.healthy is False
    assert status.last_error == "DB connection drop"

    # Manually recover
    hierarchy.report_success("passive")
    assert status.state == CircuitState.CLOSED
    assert status.healthy is True
    assert status.failure_count == 0


# ---------------------------------------------------------------------------
# Lifecycle & Shutdown Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shutdown_all_executes_async_close(hierarchy):
    mock_async_close = AsyncMock()

    class AsyncSubsystem:
        async def close(self):
            await mock_async_close()

    subsystem = AsyncSubsystem()
    hierarchy.register("closable", subsystem)

    await hierarchy.shutdown_all()

    mock_async_close.assert_awaited_once()
    assert len(hierarchy.list_subsystems()) == 0


@pytest.mark.asyncio
async def test_health_check_timeout_handling(hierarchy):
    async def slow_health_check():
        await asyncio.sleep(5.0)
        return True

    hierarchy.register("slow_subsystem", slow_health_check)

    # Overwrite check_timeout to 0.1s for test speed
    hierarchy._check_timeout = 0.1

    healthy = await hierarchy.check_health("slow_subsystem")
    assert healthy is False
    assert hierarchy.get_status("slow_subsystem").last_error == "Timed out after 0.1s"
