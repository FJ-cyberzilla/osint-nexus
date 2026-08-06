from osint_nexus.core.browser.detector import EngineType, detect_best_engine
from osint_nexus.core.browser.engine_playwright import PlaywrightBrowserEngine


class MockLogger:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def log(self, data: dict) -> None:
        self.events.append(data)


def test_platform_detector_returns_valid_type() -> None:
    engine_type = detect_best_engine()
    assert isinstance(engine_type, EngineType)


def test_playwright_engine_fallback_processing() -> None:
    logger = MockLogger()
    profiles: list[dict] = []

    engine = PlaywrightBrowserEngine(telemetry_client=logger, callback=lambda p: profiles.append(p))

    sample_json = '{"webgl_renderer": "Adreno (TM) 740", "cpu_benchmark_ms": 14.2}'
    engine.handle_submit_telemetry(None, sample_json)

    assert len(logger.events) == 1
    assert logger.events[0]["webgl_renderer"] == "Adreno (TM) 740"
    assert len(profiles) == 1
    # Assuming the inference engine maps this to High-End based on common device inference logic
    assert profiles[0]["hardware_tier"] == "High-End"
    assert profiles[0]["anomaly_detected"] is False
