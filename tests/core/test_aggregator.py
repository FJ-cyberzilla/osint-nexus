from osint_nexus.core.aggregator import FullFingerprintEngine
from osint_nexus.core.detectors.http import HttpFingerprintStrategy
from osint_nexus.core.detectors.registry import FingerprintStrategyRegistry
from osint_nexus.core.detectors.tls import TlsFingerprintStrategy
from osint_nexus.core.type_defs import to_json_value


def test_aggregator():
    registry = FingerprintStrategyRegistry()
    registry.register(HttpFingerprintStrategy())
    registry.register(TlsFingerprintStrategy())

    engine = FullFingerprintEngine(registry)

    telemetry_data = {"http_headers": {"sec-ch-ua-platform": "Windows"}, "tls_ja3": "mock_ja3_hash"}

    result = engine.aggregate(to_json_value(telemetry_data))

    assert "aggregated_data" in result
    assert "final_confidence" in result
    assert 0.0 <= result["final_confidence"] <= 1.0
