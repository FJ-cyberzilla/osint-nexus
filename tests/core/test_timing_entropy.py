import pytest

from osint_nexus.core.detectors.timing_entropy import TimingEntropyDetector


@pytest.mark.asyncio
async def test_timing_entropy_detector() -> None:
    detector = TimingEntropyDetector()
    assert detector.name == "timing_entropy"

    assert await detector.analyze({"pixel_entropy_distribution": 5.0}) == 1.0
    assert await detector.analyze({"pixel_entropy_distribution": 4.0}) == 0.0
    assert await detector.analyze({}) == 0.0
