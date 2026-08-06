from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from osint_nexus.core.captcha.base import CaptchaConfig
from osint_nexus.core.captcha.solvers.two_captcha import TwoCaptchaSolver


@pytest.fixture
def mock_config():
    config = MagicMock(spec=CaptchaConfig)
    config.two_captcha_key = "test_key"
    config.poll_interval = 0.1
    config.solve_timeout = 1.0
    return config


@pytest.mark.asyncio
async def test_two_captcha_health_check_success(mock_config):
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.text.return_value = '{"status": 1, "request": "10.0"}'
        mock_resp.__aenter__.return_value = mock_resp
        mock_get.return_value = mock_resp

        solver = TwoCaptchaSolver(mock_config)
        assert await solver.health_check() is True
