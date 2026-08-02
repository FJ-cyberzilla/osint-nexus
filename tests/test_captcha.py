import pytest

from osint_nexus.core.captcha.base import CaptchaBudgetExceeded, CaptchaConfig, CaptchaServiceError
from osint_nexus.core.captcha.solvers.anti_captcha import AntiCaptchaSolver


@pytest.mark.asyncio
async def test_anti_captcha_zero_balance_error() -> None:
    config = CaptchaConfig(anti_captcha_key="test_key")
    solver = AntiCaptchaSolver(config)

    # Mock _handle_poll_response scenario
    # Actually I need to mock the response data
    data = {"errorId": 1, "errorCode": "ERROR_ZERO_BALANCE", "errorDescription": "Balance too low"}

    with pytest.raises(CaptchaBudgetExceeded):
        solver._handle_poll_response(data, 0)


@pytest.mark.asyncio
async def test_anti_captcha_invalid_key_error() -> None:
    config = CaptchaConfig(anti_captcha_key="test_key")
    solver = AntiCaptchaSolver(config)

    # Mock _handle_poll_response scenario
    data = {"errorId": 1, "errorCode": "ERROR_KEY_DOES_NOT_EXIST", "errorDescription": "Invalid Key"}

    with pytest.raises(CaptchaServiceError, match="Invalid API key"):
        solver._handle_poll_response(data, 0)
