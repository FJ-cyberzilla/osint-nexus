from unittest.mock import MagicMock

import pytest

from osint_nexus.core.detection import DetectionEngine
from osint_nexus.core.evasion import EvasionWeights
from osint_nexus.core.report import TelemetryPayload


def test_ai_user_agent_detection():
    weights = EvasionWeights(
        novel_detector_weight=0.1,
        platform_density_threshold=5,
        platform_density_penalty=0.1,
        degraded_pipeline_penalty=0.1,
        ai_signature=0.2,
        headless_mode=0.2,
        webdriver_active=0.2,
        automation_plugins=0.2,
    )
    engine = DetectionEngine(weights)

    assert engine._has_ai_user_agent("Mozilla/5.0 (compatible; GPTBot/1.0)") is True
    assert engine._has_ai_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") is False


def test_browser_signatures():
    weights = EvasionWeights(
        novel_detector_weight=0.1,
        platform_density_threshold=5,
        platform_density_penalty=0.1,
        degraded_pipeline_penalty=0.1,
        ai_signature=0.2,
        headless_mode=0.2,
        webdriver_active=0.2,
        automation_plugins=0.2,
    )
    engine = DetectionEngine(weights)

    browser = MagicMock()
    browser.user_agent = "Mozilla/5.0"
    browser.headless = True
    browser.webdriver = False
    browser.automation_plugins = True

    payload = TelemetryPayload(browser=browser, raw_metadata={}, pipeline_status="ok")

    score = engine._check_browser_signatures(payload)
    # headless (0.2) + automation_plugins (0.2) = 0.4
    assert pytest.approx(score) == 0.4
