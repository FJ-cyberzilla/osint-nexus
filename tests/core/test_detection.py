from typing import Any
from unittest.mock import MagicMock

import pytest

from osint_nexus.core.detection import DetectionEngine
from osint_nexus.core.evasion import EvasionWeights
from osint_nexus.core.report import TelemetryPayload


def test_ai_user_agent_detection() -> None:
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


def test_browser_signatures() -> None:
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


@pytest.mark.asyncio
async def test_analyze() -> None:
    weights = EvasionWeights(
        novel_detector_weight=0.1,
        platform_density_threshold=1,
        platform_density_penalty=0.1,
        degraded_pipeline_penalty=0.1,
        ai_signature=0.0,
        headless_mode=0.0,
        webdriver_active=0.0,
        automation_plugins=0.0,
    )
    engine = DetectionEngine(weights)

    browser = MagicMock()
    browser.user_agent = "Mozilla/5.0"
    browser.headless = False
    browser.webdriver = False
    browser.automation_plugins = False
    payload = TelemetryPayload(browser=browser, raw_metadata={}, pipeline_status="degraded")

    # platform_density_penalty (0.1) + degraded_pipeline_penalty (0.1) = 0.2
    result = await engine.analyze(payload, ["p1", "p2"])
    assert pytest.approx(result.evasion_score) == 0.2
    assert result.is_automated is False


@pytest.mark.asyncio
async def test_run_novel_detectors() -> None:
    weights = EvasionWeights(
        novel_detector_weight=0.5,
        platform_density_threshold=5,
        platform_density_penalty=0.0,
        degraded_pipeline_penalty=0.0,
        ai_signature=0.0,
        headless_mode=0.0,
        webdriver_active=0.0,
        automation_plugins=0.0,
    )

    # Define an async function for the mock's analyze method
    async def mock_analyze(metadata: Any) -> float:
        return 0.2

    mock_detector = MagicMock()
    mock_detector.name = "mock_detector"
    mock_detector.analyze = mock_analyze  # Assign the async function

    engine = DetectionEngine(weights, detectors=[mock_detector])

    payload = TelemetryPayload(browser=None, raw_metadata={"k": "v"}, pipeline_status="ok")
    details: dict[str, float] = {}

    # (1.0 - 0.2) * 0.5 = 0.4
    score = await engine._run_novel_detectors(payload, details)
    assert pytest.approx(score) == 0.4
    assert details["mock_detector"] == 0.2
