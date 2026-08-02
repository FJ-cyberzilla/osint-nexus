import asyncio

import pytest

from osint_nexus.core.hierarchy import HierarchyManager


class MockSubsystem:
    def __init__(self, healthy: bool = True) -> None:
        self.healthy = healthy
        self.shutdown_called = False

    async def health_check(self) -> bool:
        return self.healthy

    async def shutdown(self) -> None:
        self.shutdown_called = True


@pytest.mark.asyncio
async def test_hierarchy_manager() -> None:
    manager = HierarchyManager()
    subsystem = MockSubsystem()

    manager.register("test", subsystem)
    assert manager.get_status("test") is not None
    assert manager.list_subsystems()["test"] is True

    # Test health check
    result = await manager.check_health("test")
    assert result is True

    # Test failure reporting
    manager.report_failure("test")
    assert manager.list_subsystems()["test"] is False

    # Test success reporting
    manager.report_success("test")
    assert manager.list_subsystems()["test"] is True

    # Test unregistering
    await manager.unregister("test")
    assert manager.get_status("test") is None
    assert subsystem.shutdown_called


@pytest.mark.asyncio
async def test_circuit_breaker() -> None:
    manager = HierarchyManager(failure_threshold=2)
    subsystem = MockSubsystem(healthy=False)

    manager.register("failing", subsystem)

    # Check 1: Still considered healthy, but failure count increases
    await manager.check_health("failing")
    status = manager.get_status("failing")
    assert status is not None
    assert status.failure_count == 1

    # Check 2: Circuit should open
    await manager.check_health("failing")
    status = manager.get_status("failing")
    assert status is not None
    assert status.circuit_open is True

    # Check 3: Should return False immediately due to open circuit
    result = await manager.check_health("failing")
    assert result is False


@pytest.mark.asyncio
async def test_check_all() -> None:
    manager = HierarchyManager()
    s1 = MockSubsystem(healthy=True)
    s2 = MockSubsystem(healthy=False)
    manager.register("s1", s1)
    manager.register("s2", s2)

    results = await manager.check_all()
    assert results["s1"] is True
    assert results["s2"] is False


@pytest.mark.asyncio
async def test_monitoring_loop() -> None:
    manager = HierarchyManager(check_interval=0.1)
    subsystem = MockSubsystem()
    manager.register("test", subsystem)

    await manager.start_monitoring()
    assert manager._running is True
    assert manager._monitor_task is not None

    await asyncio.sleep(0.2)  # Allow loop to run
    await manager.stop_monitoring()
    assert manager._running is False
    assert manager._monitor_task is None


@pytest.mark.asyncio
async def test_shutdown_all() -> None:
    manager = HierarchyManager()
    s1 = MockSubsystem()
    s2 = MockSubsystem()
    manager.register("s1", s1)
    manager.register("s2", s2)

    await manager.shutdown_all()
    assert s1.shutdown_called
    assert s2.shutdown_called
    assert manager.list_subsystems() == {}
