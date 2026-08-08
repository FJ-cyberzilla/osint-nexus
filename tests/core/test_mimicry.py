from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from osint_nexus.core.mimicry import Activity, HumanMimicryEngine


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.TYPING_CHAR_MIN = 0.05
    config.TYPING_CHAR_MAX = 0.3
    config.CLICK_HESITATION_PROB = 0.4
    config.CLICK_MISCLICK_PROB = 0.08
    return config


@pytest.mark.asyncio
async def test_mimicry_engine_delay(mock_config):
    engine = HumanMimicryEngine(mock_config)
    # Test that human_delay returns a value
    # We need to mock asyncio.sleep
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        delay = await engine.human_delay(Activity.PAGE_LOAD)
        assert delay > 0


@pytest.mark.asyncio
async def test_mimicry_typing_delay(mock_config):
    engine = HumanMimicryEngine(mock_config)
    # Mock asyncio.sleep
    with patch("asyncio.sleep", new_callable=AsyncMock):
        total = await engine.typing_delay(5)
        assert total >= 0
