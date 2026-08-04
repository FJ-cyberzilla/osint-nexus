from osint_nexus.core.telemetry import TelemetryProbe, TelemetryRegistry


class MockProbe(TelemetryProbe):
    def run(self):
        return {"data": "test_value"}


def test_telemetry_registry():
    registry = TelemetryRegistry()
    probe = MockProbe()
    registry.register_probe("mock", probe)

    results = registry.run_all()
    assert "mock" in results
    assert results["mock"] == {"data": "test_value"}
