from osint_nexus.core.health import HealthTracker


def test_health_tracker() -> None:
    tracker = HealthTracker(failure_threshold=3)

    assert tracker.is_healthy("p1")

    tracker.record_failure("p1")
    tracker.record_failure("p1")
    assert tracker.is_healthy("p1")

    tracker.record_failure("p1")
    assert not tracker.is_healthy("p1")

    tracker.record_success("p1")
    assert tracker.is_healthy("p1")

    tracker.reset("p1")
    assert tracker.is_healthy("p1")
