import pytest
import time
from osint_nexus.core.health import HealthTracker

def test_circuit_breaker_and_recovery():
    # Set a short recovery timeout for testing
    tracker = HealthTracker(failure_threshold=2, default_recovery_timeout=0.1)
    
    assert tracker.is_healthy("p1")
    
    # Trigger failure
    tracker.record_failure("p1")
    tracker.record_failure("p1")
    assert not tracker.is_healthy("p1")
    
    # Wait for recovery
    time.sleep(0.15)
    assert tracker.is_healthy("p1")
    
    # Verify success resets failure
    tracker.record_success("p1")
    assert tracker.is_healthy("p1")

def test_per_provider_timeout():
    tracker = HealthTracker(failure_threshold=1, default_recovery_timeout=1.0)
    
    # Fast recovery provider
    tracker.set_provider_timeout("fast_provider", 0.05)
    
    tracker.record_failure("fast_provider")
    assert not tracker.is_healthy("fast_provider")
    
    time.sleep(0.1)
    assert tracker.is_healthy("fast_provider")
