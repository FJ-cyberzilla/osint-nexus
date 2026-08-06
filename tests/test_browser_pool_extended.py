from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from osint_nexus.core.browser.pool import BrowserPoolError, BrowserPoolManager, BrowserPoolState


@pytest.mark.asyncio
@patch("osint_nexus.core.browser.pool.PLAYWRIGHT_AVAILABLE", True)
@patch("osint_nexus.core.browser.pool.async_playwright")
async def test_browser_pool_initialize_success(mock_playwright):
    # Mocking async_playwright() -> factory -> start() -> playwright_instance
    mock_pw_instance = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.start = AsyncMock(return_value=mock_pw_instance)
    mock_playwright.return_value = mock_factory

    bpm = BrowserPoolManager()
    await bpm.initialize()

    assert bpm._state == BrowserPoolState.READY
    assert bpm._playwright == mock_pw_instance
    await bpm.close()


@pytest.mark.asyncio
async def test_browser_pool_initialize_fails_without_playwright():
    with patch("osint_nexus.core.browser.pool.PLAYWRIGHT_AVAILABLE", False):
        bpm = BrowserPoolManager()
        with pytest.raises(BrowserPoolError):
            await bpm.initialize()


@pytest.mark.asyncio
@patch("osint_nexus.core.browser.pool.PLAYWRIGHT_AVAILABLE", True)
@patch("osint_nexus.core.browser.pool.async_playwright")
async def test_acquire_context_auto_init(mock_playwright):
    bpm = BrowserPoolManager()

    # Mocking browser and factory to avoid actual calls
    bpm._browser = AsyncMock()
    bpm._factory = AsyncMock()
    bpm._state = BrowserPoolState.READY

    async with bpm.acquire_context():
        assert bpm._factory.create.called
