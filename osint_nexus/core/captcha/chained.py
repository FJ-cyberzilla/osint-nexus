from __future__ import annotations

import logging
from typing import Any

import aiohttp

from osint_nexus.core.captcha.base import CaptchaSolver
from osint_nexus.core.captcha.config import CaptchaConfig
from osint_nexus.core.captcha.exceptions import CaptchaError
from osint_nexus.core.captcha.models import CaptchaSolveResult, CaptchaType

logger = logging.getLogger("osint_nexus.captcha")


class ChainedCaptchaSolver(CaptchaSolver):
    def __init__(
        self,
        solvers: list[CaptchaSolver],
        config: CaptchaConfig,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__("chain", config, session)
        self.solvers = solvers

    async def health_check(self) -> bool:
        for solver in self.solvers:
            if await solver.health_check():
                return True
        return False

    def estimate_cost(self, _captcha_type: CaptchaType) -> float:
        return min(s.estimate_cost(_captcha_type) for s in self.solvers)

    async def _solve_impl(
        self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: Any
    ) -> CaptchaSolveResult:
        last_error = None
        for solver in self.solvers:
            try:
                result = await solver.solve(site_key, url, captcha_type, **kwargs)
                if result.success:
                    return result
                last_error = result.error
            except CaptchaError as e:
                last_error = str(e)
                logger.warning("Solver %s failed: %s", solver.name, e)
                continue
        return CaptchaSolveResult(error=f"All solvers failed. Last error: {last_error}")
