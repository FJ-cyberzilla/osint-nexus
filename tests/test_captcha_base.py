from typing import Any
from unittest.mock import AsyncMock

import pytest

from osint_nexus.core.captcha.base import (
    CaptchaBudgetExceeded,
    CaptchaConfig,
    CaptchaSolver,
    CaptchaSolveResult,
    CaptchaType,
)


class MockSolver(CaptchaSolver):
    async def health_check(self) -> bool:
        return True

    async def _solve_impl(
        self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: Any
    ) -> CaptchaSolveResult:
        return CaptchaSolveResult(token="mock_token", cost=0.1)

    def estimate_cost(self, captcha_type: CaptchaType) -> float:
        return 0.05


def test_captcha_config_defaults():
    config = CaptchaConfig()
    assert config.max_retries == 3
    assert config.solve_timeout == 120.0


def test_captcha_solver_budget_check():
    config = CaptchaConfig(max_cost_per_solve=0.01, daily_budget=0.05)
    solver = MockSolver("mock", config)

    # Cost (0.05) > max_cost_per_solve (0.01)
    with pytest.raises(CaptchaBudgetExceeded):
        solver._check_budget(CaptchaType.RECAPTCHA_V2)


@pytest.mark.asyncio
async def test_captcha_solver_retry_logic():
    config = CaptchaConfig(max_retries=2, retry_delay=0.01)
    solver = MockSolver("mock", config)

    # Mock _perform_attempt to fail then succeed
    solver._perform_attempt = AsyncMock(side_effect=[None, CaptchaSolveResult(token="success")])


@pytest.mark.asyncio
async def test_chained_captcha_solver():
    config = CaptchaConfig()
    solver1 = MockSolver("s1", config)
    solver2 = MockSolver("s2", config)
    solver2._solve_impl = AsyncMock(return_value=CaptchaSolveResult(token="success2"))

    # Setup chain to fail s1, succeed s2
    solver1._solve_impl = AsyncMock(return_value=CaptchaSolveResult(error="fail"))

    from osint_nexus.core.captcha.base import ChainedCaptchaSolver

    chain = ChainedCaptchaSolver([solver1, solver2], config)

    result = await chain._solve_impl("key", "url", CaptchaType.RECAPTCHA_V2)
    assert result.token == "success2"
    assert solver1._solve_impl.called
    assert solver2._solve_impl.called
