import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock dependencies before importing
sys.modules["osint_nexus.core.browser.config"] = MagicMock()
sys.modules["osint_nexus.core.browser.factory"] = MagicMock()
sys.modules["osint_nexus.core.browser.monitor"] = MagicMock()

from osint_nexus.core.browser.pool import BrowserPoolError, BrowserPoolManager, BrowserPoolState  # noqa: E402


@pytest.mark.asyncio
async def test_browser_pool_initialize_not_available() -> None:
    # Force PLAYWRIGHT_AVAILABLE to False
    with patch("osint_nexus.core.browser.pool.PLAYWRIGHT_AVAILABLE", False):
        pool = BrowserPoolManager()
        with pytest.raises(BrowserPoolError, match="Playwright is not installed."):
            await pool.initialize()


@pytest.mark.asyncio
async def test_browser_pool_initialize_ready() -> None:
    with patch("osint_nexus.core.browser.pool.PLAYWRIGHT_AVAILABLE", True):
        pool = BrowserPoolManager()
        pool._state = BrowserPoolState.READY
        await pool.initialize()  # Should return immediately
        assert pool._state == BrowserPoolState.READY


@pytest.mark.asyncio
async def test_browser_pool_close() -> None:
    pool = BrowserPoolManager()
    pool._state = BrowserPoolState.READY
    pool._browser = AsyncMock()
    pool._playwright = AsyncMock()

    await pool.close()
    assert pool._state == BrowserPoolState.CLOSED
    assert pool._browser is None
    assert pool._playwright is None
