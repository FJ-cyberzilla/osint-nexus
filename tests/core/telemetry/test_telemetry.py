import pytest

from osint_nexus.core.telemetry import TelemetryProbe, TelemetryRegistry


class MockProbe(TelemetryProbe):
    async def run(self):
        return {"data": "test_value"}


@pytest.mark.asyncio
async def test_telemetry_registry():
    registry = TelemetryRegistry()
    probe = MockProbe()
    registry.register_probe("mock", probe)

    results = await registry.run_all()
    assert "mock" in results
    assert results["mock"] == {"data": "test_value"}
