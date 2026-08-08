import asyncio

import pytest

from osint_nexus.core.health import HealthTracker


@pytest.mark.asyncio
async def test_circuit_breaker_and_recovery() -> None:
    # Set a short recovery timeout for testing
    tracker = HealthTracker(failure_threshold=2, default_recovery_timeout=0.1)

    assert await tracker.is_healthy("p1")

    # Trigger failure
    await tracker.record_failure("p1")
    await tracker.record_failure("p1")
    assert not await tracker.is_healthy("p1")

    # Wait for recovery
    await asyncio.sleep(0.15)
    assert await tracker.is_healthy("p1")

    # Verify success resets failure
    await tracker.record_success("p1")
    assert await tracker.is_healthy("p1")


@pytest.mark.asyncio
async def test_per_provider_timeout() -> None:
    tracker = HealthTracker(failure_threshold=1, default_recovery_timeout=1.0)

    # Fast recovery provider
    tracker.set_provider_timeout("fast_provider", 0.05)

    await tracker.record_failure("fast_provider")
    assert not await tracker.is_healthy("fast_provider")

    await asyncio.sleep(0.1)
    assert await tracker.is_healthy("fast_provider")
