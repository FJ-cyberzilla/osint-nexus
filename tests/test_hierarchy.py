import pytest

from osint_nexus.core.hierarchy import HierarchyManager


class MockSubsystem:
    def __init__(self, healthy=True):
        self.healthy = healthy
        self.shutdown_called = False

    async def health_check(self) -> bool:
        return self.healthy

    async def shutdown(self):
        self.shutdown_called = True


@pytest.mark.asyncio
async def test_hierarchy_manager():
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
async def test_circuit_breaker():
    manager = HierarchyManager(failure_threshold=2)
    subsystem = MockSubsystem(healthy=False)

    manager.register("failing", subsystem)

    # Check 1: Still considered healthy, but failure count increases
    await manager.check_health("failing")
    assert manager.get_status("failing").failure_count == 1

    # Check 2: Circuit should open
    await manager.check_health("failing")
    assert manager.get_status("failing").circuit_open is True

    # Check 3: Should return False immediately due to open circuit
    result = await manager.check_health("failing")
    assert result is False
