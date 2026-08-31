from typing import Any

from osint_nexus.core.device_inference import DeviceInferenceEngine
from osint_nexus.core.type_defs import to_json_value


def test_device_inference_engine_integration():
    from osint_nexus.core.detectors.http import HttpFingerprintStrategy
    from osint_nexus.core.detectors.registry import FingerprintStrategyRegistry
    from osint_nexus.core.detectors.tcp import TcpFingerprintStrategy
    from osint_nexus.core.detectors.tls import TlsFingerprintStrategy

    registry = FingerprintStrategyRegistry()
    registry.register(HttpFingerprintStrategy())
    registry.register(TlsFingerprintStrategy())
    registry.register(TcpFingerprintStrategy())

    engine = DeviceInferenceEngine(registry=registry)

    # Mock data for all strategies
    mock_data: dict[str, Any] = {
        "headers": {
            "sec-ch-ua-platform": "Windows",
            "sec-ch-ua-mobile": "?0",
        },
        "ja3_hash": "72a589da586844d7f0818ce684948eea",
        "tcp": {"ttl": 128, "tcp_options": ["wscale"]},
    }

    # Strategy extraction test (simulated integration)
    results = {}
    for strategy in engine.registry.get_all():
        if strategy.name == "http_headers":
            results[strategy.name] = strategy.extract(to_json_value(mock_data.get("headers")))
        elif strategy.name == "tls_ja3":
            results[strategy.name] = strategy.extract(to_json_value({"ja3_hash": mock_data.get("ja3_hash")}))
        elif strategy.name == "tcp_stack":
            results[strategy.name] = strategy.extract(to_json_value(mock_data.get("tcp")))

    assert "http_headers" in results
    assert "tls_ja3" in results
    assert "tcp_stack" in results

    assert results["http_headers"]["data"]["platform"] == "Windows"
    assert results["tls_ja3"]["data"]["inferred_device"] == "Chrome 120 on Windows 10"
    assert results["tcp_stack"]["data"]["inferred_os"] == "Windows 10/11"


# To support the test above, I need to add a 'name' attribute to the strategy classes,
# which is missing in the current implementation.
