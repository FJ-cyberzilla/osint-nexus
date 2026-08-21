import pytest

from osint_nexus.core.config import Config
from osint_nexus.core.constants import DeviceInferenceConstants
from osint_nexus.core.fingerprint import FingerprintAgent


class TestFingerprintAgent:
    """Test suite for FingerprintAgent."""

    @pytest.fixture
    def agent(self):
        """Create fresh agent for each test."""
        return FingerprintAgent()

    def test_collect_scan_telemetry(self, agent):
        """Test telemetry collection."""
        telemetry = agent.collect_scan_telemetry("proxy_url", "user_agent_string")

        assert telemetry["proxy_node"] == "proxy_url"
        assert telemetry["agent_fingerprint"] == "user_agent_string"
        assert "scan_timestamp" in telemetry

    def test_infer_known_device(self, agent):
        """Test that known devices are correctly identified."""
        result = agent.infer_target_device("This is an iPhone device")

        assert result["device_model"] == "iPhone"
        assert result["os_family"] == "iOS"
        assert result["confidence"] == DeviceInferenceConstants.REGEX_MATCH_CONFIDENCE
        assert "iPhone" in result["matches"]

    def test_infer_unknown_device(self, agent):
        """Test that unknown devices return unidentified."""
        result = agent.infer_target_device("Unknown device")

        assert result["device_model"] == DeviceInferenceConstants.UNIDENTIFIED
        assert result["os_family"] == DeviceInferenceConstants.UNIDENTIFIED
        assert result["confidence"] == DeviceInferenceConstants.MIN_CONFIDENCE

    def test_infer_empty_content(self, agent):
        """Test handling of empty content."""
        result = agent.infer_target_device("")

        assert result["device_model"] == DeviceInferenceConstants.UNIDENTIFIED
        assert result["confidence"] == DeviceInferenceConstants.MIN_CONFIDENCE

    def test_infer_handles_malformed_input(self, agent):
        """Test graceful handling of malformed input."""
        malformed_inputs = [None, {}, [], 123, object()]

        for input_data in malformed_inputs:
            # Should not raise exception
            result = agent.infer_target_device(input_data)
            assert result["device_model"] == DeviceInferenceConstants.UNIDENTIFIED
            assert result["confidence"] == DeviceInferenceConstants.MIN_CONFIDENCE

    def test_load_custom_patterns(self):
        """Test loading custom patterns."""
        # Setup mock config
        mock_config = Config()
        mock_config.device_patterns = [(r"CustomDevice", "CustomModel", "CustomOS")]

        agent = FingerprintAgent(config=mock_config)

        # Test custom match
        result = agent.infer_target_device("This is a CustomDevice")
        assert result["device_model"] == "CustomModel"
        assert result["os_family"] == "CustomOS"
        assert result["confidence"] == DeviceInferenceConstants.REGEX_MATCH_CONFIDENCE

    def test_collect_all_fingerprints(self, agent):
        """Test aggregation of all strategies."""
        test_data = {"user-agent": "Mozilla/5.0", "ttl": 128, "tcp_options": ["wscale"]}

        result = agent.collect_all_fingerprints(test_data)

        assert "fingerprints" in result
        assert "http_headers" in result["fingerprints"]
        assert "tcp_stack" in result["fingerprints"]
        assert result["combined_confidence"] > 0.0

    def test_collect_all_fingerprints_with_ja3(self):
        """Test aggregation of all strategies with injected JA3."""
        from osint_nexus.core.type_defs import JSONValue

        ja3_hash = "72a589da586844d7f0818ce684948eea"
        agent = FingerprintAgent(ja3_hash=ja3_hash)
        test_data: dict[str, JSONValue] = {"user-agent": "Mozilla/5.0"}

        result = agent.collect_all_fingerprints(test_data)

        assert "fingerprints" in result
        assert "tls_ja3" in result["fingerprints"]

        # Need to cast for mypy as fingerprint results are `JSONValue`
        tls_data = result["fingerprints"]["tls_ja3"]
        assert isinstance(tls_data, dict)
        assert tls_data["ja3_hash"] == ja3_hash
        assert "inferred_device" in tls_data
