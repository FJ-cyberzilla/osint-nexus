import pytest

from osint_nexus.core.health import HealthTracker


@pytest.mark.asyncio
async def test_health_tracker() -> None:
    tracker = HealthTracker(failure_threshold=3)

    assert await tracker.is_healthy("p1")

    await tracker.record_failure("p1")
    await tracker.record_failure("p1")
    assert await tracker.is_healthy("p1")

    await tracker.record_failure("p1")
    assert not await tracker.is_healthy("p1")

    await tracker.record_success("p1")
    assert await tracker.is_healthy("p1")

    tracker.reset("p1")
    assert await tracker.is_healthy("p1")
