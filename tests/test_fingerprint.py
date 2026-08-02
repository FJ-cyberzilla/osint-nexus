from osint_nexus.core.config import Config
from osint_nexus.core.fingerprint import FingerprintAgent


def test_collect_scan_telemetry() -> None:
    agent = FingerprintAgent()
    telemetry = agent.collect_scan_telemetry("proxy_url", "user_agent_string")

    assert telemetry["proxy_node"] == "proxy_url"
    assert telemetry["agent_fingerprint"] == "user_agent_string"
    assert "scan_timestamp" in telemetry


def test_infer_target_device() -> None:
    agent = FingerprintAgent()

    # Test match
    result = agent.infer_target_device("This is an iPhone device")
    assert result["device_model"] == "iPhone"
    assert result["os_family"] == "iOS"


def test_analyze_request_headers() -> None:
    agent = FingerprintAgent()
    # Test no match
    result_none = agent.infer_target_device("Unknown device")
    assert result_none["device_model"] == "Unknown"
    assert result_none["os_family"] == "Unknown"
    assert result_none["confidence"] == 0.0


def test_load_custom_patterns() -> None:
    # Setup mock config
    mock_config = Config()
    mock_config.device_patterns = [(r"CustomDevice", "CustomModel", "CustomOS")]

    agent = FingerprintAgent(config=mock_config)

    # Test custom match
    result = agent.infer_target_device("This is a CustomDevice")
    assert result["device_model"] == "CustomModel"
    assert result["os_family"] == "CustomOS"
