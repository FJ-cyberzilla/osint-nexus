from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from osint_nexus.core.captcha.base import CaptchaConfig, CaptchaType
from osint_nexus.core.captcha.exceptions import CaptchaTimeoutError
from osint_nexus.core.captcha.solvers.anti_captcha import AntiCaptchaSolver


@pytest.fixture
def mock_config():
    config = MagicMock(spec=CaptchaConfig)
    config.anti_captcha_key = "test_key"
    config.poll_interval = 0.1
    config.solve_timeout = 1.0
    return config


@pytest.mark.asyncio
async def test_anti_captcha_health_check_success(mock_config):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.json.return_value = {"balance": 1.0}
        mock_resp.__aenter__.return_value = mock_resp
        mock_post.return_value = mock_resp

        solver = AntiCaptchaSolver(mock_config)
        assert await solver.health_check() is True


@pytest.mark.asyncio
async def test_anti_captcha_solve_poll_timeout(mock_config):
    with patch("aiohttp.ClientSession.post") as mock_post:
        # Task creation
        mock_resp1 = AsyncMock()
        mock_resp1.json.return_value = {"errorId": 0, "taskId": 123}
        mock_resp1.__aenter__.return_value = mock_resp1

        # Poll response (not ready)
        mock_resp2 = AsyncMock()
        mock_resp2.json.return_value = {"status": "processing", "errorId": 0}
        mock_resp2.__aenter__.return_value = mock_resp2

        calls = 0

        def mock_post_side_effect(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return mock_resp1
            return mock_resp2

        mock_post.side_effect = mock_post_side_effect

        solver = AntiCaptchaSolver(mock_config)
        # We need to mock asyncio.sleep to be fast
        with patch("asyncio.sleep", new_callable=AsyncMock), pytest.raises(CaptchaTimeoutError):
            await solver._solve_impl("key", "url", CaptchaType.RECAPTCHA_V2)
