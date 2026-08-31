from osint_nexus.core.detectors.cdn import CdnFingerprintStrategy
from osint_nexus.core.detectors.client_validator import ClientFingerprintValidator
from osint_nexus.core.detectors.dns import DnsFingerprintStrategy
from osint_nexus.core.detectors.extensions import ExtensionFingerprintStrategy
from osint_nexus.core.detectors.http2 import Http2FingerprintStrategy
from osint_nexus.core.detectors.timezone import TimezoneFingerprintStrategy
from osint_nexus.core.type_defs import to_json_value


def test_http2_detector():
    strategy = Http2FingerprintStrategy()
    data = {"alpn": "h2", "settings_frame": {3: 200}}
    result = strategy.extract(to_json_value(data))

    assert result["name"] == "http2_3_stack"
    assert result["data"]["protocol"] == "h2"
    assert result["confidence"] == 0.7


def test_dns_detector():
    strategy = DnsFingerprintStrategy()
    data = {"resolver_ip": "8.8.8.8", "query_types": ["A", "AAAA"]}
    result = strategy.extract(to_json_value(data))

    assert result["name"] == "dns_patterns"
    assert result["data"]["resolver"] == "8.8.8.8"
    assert result["confidence"] == 0.6


def test_timezone_detector():
    strategy = TimezoneFingerprintStrategy()
    data = {"timezone": "UTC", "offset_seconds": 0}
    result = strategy.extract(to_json_value(data))

    assert result["name"] == "timezone_ntp"
    assert result["data"]["timezone"] == "UTC"
    assert result["confidence"] == 0.5


def test_extensions_detector():
    strategy = ExtensionFingerprintStrategy()
    data = {"detected_extensions": ["uBlock Origin"]}
    result = strategy.extract(to_json_value(data))

    assert result["name"] == "extension_load"
    assert result["data"]["has_adblocker"] is True
    assert result["confidence"] == 0.8


def test_cdn_detector():
    strategy = CdnFingerprintStrategy()
    data = {"server_headers": {"cf-ray": "123"}}
    result = strategy.extract(to_json_value(data))

    assert result["name"] == "cdn_headers"
    assert result["data"]["cdn_detected"] is True
    assert result["confidence"] == 0.75


def test_client_metric_validator():
    strategy = ClientFingerprintValidator()
    data = {"font_fingerprint": "a1b2c3d4", "canvas_hash": "e5f6g7h8"}
    result = strategy.extract(to_json_value(data))

    assert result["name"] == "client_metrics"
    assert result["data"]["font_fp"] == "a1b2c3d4"
    assert result["confidence"] == 0.5
