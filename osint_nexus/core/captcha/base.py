from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

import aiohttp

from osint_nexus.core.captcha.config import CaptchaConfig
from osint_nexus.core.captcha.exceptions import (
    CaptchaBudgetExceeded,
    CaptchaError,
    CaptchaServiceError,
    CaptchaTimeoutError,
)
from osint_nexus.core.captcha.models import CaptchaSolveResult, CaptchaType
from osint_nexus.core.types import JSONValue
from osint_nexus.utils.security import SecurityUtility

logger = logging.getLogger("osint_nexus.captcha")

__all__ = [
    "CaptchaSolver",
    "CaptchaConfig",
    "CaptchaError",
    "CaptchaBudgetExceeded",
    "CaptchaServiceError",
    "CaptchaTimeoutError",
    "CaptchaSolveResult",
    "CaptchaType",
    "CaptchaSolverProtocol",
]


@runtime_checkable
class CaptchaSolverProtocol(Protocol):
    async def health_check(self) -> bool: ...
    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        **kwargs: JSONValue,
    ) -> CaptchaSolveResult: ...
    async def close(self) -> None: ...


class CaptchaSolver(CaptchaSolverProtocol, ABC):
    def __init__(
        self, name: str, config: CaptchaConfig, session: aiohttp.ClientSession | None = None
    ) -> None:
        self.name = name
        self.config = config
        self._session = session
        self._total_cost: float = 0.0

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    async def _solve_impl(
        self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: JSONValue
    ) -> CaptchaSolveResult:
        pass

    @abstractmethod
    def estimate_cost(self, captcha_type: CaptchaType) -> float:
        pass

    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        **kwargs: JSONValue,
    ) -> CaptchaSolveResult:
        self._check_budget(captcha_type)
        return await self._retry_solve_impl(site_key, url, captcha_type, **kwargs)

    def _check_budget(self, captcha_type: CaptchaType) -> None:
        est_cost = self.estimate_cost(captcha_type)
        if self.config.cost_tracking:
            if est_cost > self.config.max_cost_per_solve:
                raise CaptchaBudgetExceeded(
                    f"Estimated cost {est_cost:.4f} exceeds max {self.config.max_cost_per_solve:.4f}"
                )
            if self._total_cost + est_cost > self.config.daily_budget:
                raise CaptchaBudgetExceeded("Daily budget exceeded")

    async def _retry_solve_impl(
        self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: JSONValue
    ) -> CaptchaSolveResult:
        for attempt in range(self.config.max_retries):
            result = await self._perform_attempt(attempt, site_key, url, captcha_type, kwargs)
            if result:
                return result
        raise CaptchaError(f"Failed to solve captcha after {self.config.max_retries} attempts")

    def _handle_successful_attempt(self, result: CaptchaSolveResult) -> CaptchaSolveResult:
        """Handle successful captcha attempt."""
        if self.config.cost_tracking:
            self._total_cost += result.cost
        return result

    def _handle_attempt_error(self, exc: Exception, attempt: int) -> None:
        """Handle errors during captcha attempt."""
        if isinstance(exc, CaptchaBudgetExceeded):
            logger.error("Fatal solver error: %s", SecurityUtility.sanitize_for_log(exc))
            raise exc

        if isinstance(exc, (aiohttp.ClientError, asyncio.TimeoutError, CaptchaTimeoutError)):
            logger.warning(
                "Solver %s attempt %d failed (transient): %s",
                SecurityUtility.sanitize_for_log(self.name),
                attempt + 1,
                SecurityUtility.sanitize_for_log(exc),
            )
            return

        if isinstance(exc, CaptchaError):
            logger.warning(
                "Solver %s attempt %d failed: %s",
                SecurityUtility.sanitize_for_log(self.name),
                attempt + 1,
                SecurityUtility.sanitize_for_log(exc),
            )
        else:
            logger.error(
                "Unexpected error in solver %s: %s",
                SecurityUtility.sanitize_for_log(self.name),
                SecurityUtility.sanitize_for_log(exc),
                exc_info=True,
            )

        if attempt == self.config.max_retries - 1:
            raise

    async def _perform_attempt(
        self, attempt: int, site_key: str, url: str, captcha_type: CaptchaType, kwargs: dict[str, JSONValue]
    ) -> CaptchaSolveResult | None:
        try:
            result = await asyncio.wait_for(
                self._solve_impl(site_key, url, captcha_type, **kwargs), timeout=self.config.solve_timeout
            )
            if result.success:
                return self._handle_successful_attempt(result)

            logger.warning(
                "Solver %s returned no token on attempt %d: %s",
                SecurityUtility.sanitize_for_log(self.name),
                attempt + 1,
                SecurityUtility.sanitize_for_log(result.error),
            )
            await asyncio.sleep(self.config.retry_delay * (1.5**attempt))
        except Exception as exc:
            self._handle_attempt_error(exc, attempt)
            # Sleep logic for retriable errors
            if not isinstance(exc, CaptchaBudgetExceeded):
                delay = self.config.retry_delay * (
                    2**attempt
                    if isinstance(exc, (aiohttp.ClientError, asyncio.TimeoutError, CaptchaTimeoutError))
                    else 1.5**attempt
                )
                await asyncio.sleep(delay)
        return None

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
