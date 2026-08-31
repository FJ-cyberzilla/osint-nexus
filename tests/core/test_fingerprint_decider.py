from osint_nexus.core.fingerprint_decider import ClientFingerprintValidator, RiskLevel
from osint_nexus.core.type_defs import to_json_value


def test_legitimate_client():
    validator = ClientFingerprintValidator()

    # Test 1: Legitimate client
    legitimate = {
        "font_fingerprint": "Arial, Helvetica, sans-serif",
        "canvas_hash": "8b4c3f1a7d9e2f5c",
        "webgl_vendor": "NVIDIA Corporation",
        "timezone_offset": -300,
        "screen_width": 1920,
        "screen_height": 1080,
        "color_depth": 24,
        "audio_hash": "5f2a1e3c8d9f4b7e",
        "device_memory": 8,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "os_from_ua": "Windows",
        "os_from_metrics": "Windows",
        "languages": ["en-US", "en"],
        "ip_country": "US",
        "max_touch_points": 0,
        "resolution": "1920x1080",
    }

    result = validator.extract(to_json_value(legitimate))
    assert result["name"] == "client_metrics"
    assert result["data"]["suspicious"] is False


def test_headless_browser():
    validator = ClientFingerprintValidator()

    # Test 2: Headless browser
    headless = {
        "font_fingerprint": "Arial",
        "canvas_hash": "webgl-disabled",
        "webgl_vendor": "",
        "timezone_offset": 0,
        "screen_width": 800,
        "screen_height": 600,
        "color_depth": 0,
        "audio_hash": "",
        "device_memory": 0,
        "user_agent": "Mozilla/5.0 Headless Chrome",
        "os_from_ua": "Windows",
        "os_from_metrics": "Linux",
        "languages": ["en-US"],
        "ip_country": "US",
        "max_touch_points": 0,
        "resolution": "800x600",
    }

    result = validator.extract(to_json_value(headless))
    assert result["name"] == "client_metrics"
    assert result["data"]["suspicious"] is True

    assert result["data"]["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
