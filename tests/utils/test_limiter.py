import pytest

from osint_nexus.utils.limiter import AdaptiveRateLimiter


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_wait() -> None:
    limiter = AdaptiveRateLimiter(base_delay=0.1, max_delay=0.5)

    # Test wait with no site (uses base_delay)
    # We can't easily test the sleep duration directly without mocking,
    # but we can verify it doesn't raise errors.
    await limiter.wait()

    # Test wait with site
    await limiter.wait("github")


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_report() -> None:
    limiter = AdaptiveRateLimiter(base_delay=1.0, max_delay=30.0)
    site = "example.com"

    # Initial report (not really setting delay, just triggering logic)
    # Need to wait/trigger to see impact on subsequent waits

    # Test 429
    await limiter.report(site, 429, 0.1)
    assert limiter._site_delays[site] == 2.0

    # Test 500
    await limiter.report(site, 500, 0.1)
    assert limiter._site_delays[site] == 3.0  # 2.0 * 1.5

    # Test 200
    await limiter.report(site, 200, 0.1)
    # 3.0 * 0.95 = 2.85
    assert limiter._site_delays[site] == pytest.approx(2.85)

    # Test other
    await limiter.report(site, 404, 0.1)
    assert limiter._site_delays[site] == pytest.approx(2.85)
