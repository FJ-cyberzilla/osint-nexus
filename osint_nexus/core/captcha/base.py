from __future__ import annotations
import enum
import logging
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp
from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.captcha")

@dataclass
class CaptchaConfig:
    """Configuration for CAPTCHA solving."""
    two_captcha_key: Optional[str] = None
    anti_captcha_key: Optional[str] = None
    request_timeout: float = 30.0
    solve_timeout: float = 120.0
    poll_interval: float = 2.0
    max_cost_per_solve: float = 0.05
    daily_budget: float = 1.0
    cost_tracking: bool = True
    cache_ttl: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    solver_priority: List[str] = field(default_factory=lambda: ["2captcha", "anti_captcha"])

    @classmethod
    def from_config(cls, config: Config) -> "CaptchaConfig":
        return cls(
            two_captcha_key=config.get("captcha.two_captcha_key"),
            anti_captcha_key=config.get("captcha.anti_captcha_key"),
            request_timeout=config.get("captcha.request_timeout", 30.0),
            solve_timeout=config.get("captcha.solve_timeout", 120.0),
            max_cost_per_solve=config.get("captcha.max_cost_per_solve", 0.05),
            daily_budget=config.get("captcha.daily_budget", 1.0),
            cache_ttl=config.get("captcha.cache_ttl", 300),
            max_retries=config.get("captcha.max_retries", 3),
            retry_delay=config.get("captcha.retry_delay", 1.0),
        )

class CaptchaError(Exception): """Base CAPTCHA exception."""
class CaptchaTimeoutError(CaptchaError): """Solving took longer than allowed."""
class CaptchaBudgetExceeded(CaptchaError): """Cost limit or daily budget exceeded."""
class CaptchaServiceError(CaptchaError): """API error from the solving service."""

class CaptchaType(enum.Enum):
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE_CAPTCHA = "image"
    CUSTOM = "custom"

@dataclass
class CaptchaSolveResult:
    token: Optional[str] = None
    error: Optional[str] = None
    cost: float = 0.0
    solver_name: Optional[str] = None
    cached: bool = False
    @property
    def success(self) -> bool: return self.token is not None and not self.error

class CaptchaSolver(ABC):
    def __init__(self, name: str, config: CaptchaConfig, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.name = name
        self.config = config
        self._session = session
        self._total_cost: float = 0.0
    @abstractmethod
    async def health_check(self) -> bool: pass
    @abstractmethod
    async def _solve_impl(self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: Any) -> CaptchaSolveResult: pass
    @abstractmethod
    def estimate_cost(self, captcha_type: CaptchaType) -> float: pass
    async def solve(self, site_key: str, url: str, captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2, **kwargs: Any) -> CaptchaSolveResult:
        self._check_budget(captcha_type)
        return await self._retry_solve_impl(site_key, url, captcha_type, **kwargs)
    def _check_budget(self, captcha_type: CaptchaType) -> None:
        est_cost = self.estimate_cost(captcha_type)
        if self.config.cost_tracking:
            if est_cost > self.config.max_cost_per_solve: raise CaptchaBudgetExceeded(f"Estimated cost {est_cost:.4f} exceeds max {self.config.max_cost_per_solve:.4f}")
            if self._total_cost + est_cost > self.config.daily_budget: raise CaptchaBudgetExceeded("Daily budget exceeded")
    async def _retry_solve_impl(self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: Any) -> CaptchaSolveResult:
        for attempt in range(self.config.max_retries):
            result = await self._perform_attempt(attempt, site_key, url, captcha_type, kwargs)
            if result: return result
        raise CaptchaError(f"Failed to solve captcha after {self.config.max_retries} attempts")
    async def _perform_attempt(self, attempt: int, site_key: str, url: str, captcha_type: CaptchaType, kwargs: Dict[str, Any]) -> Optional[CaptchaSolveResult]:
        try:
            result = await asyncio.wait_for(self._solve_impl(site_key, url, captcha_type, **kwargs), timeout=self.config.solve_timeout)
            if result.success:
                if self.config.cost_tracking: self._total_cost += result.cost
                return result
            logger.warning("Solver %s returned no token on attempt %d: %s", self.name, attempt + 1, result.error)
            await asyncio.sleep(self.config.retry_delay * (1.5**attempt))
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            logger.warning("Solver %s attempt %d failed: %s", self.name, attempt + 1, exc)
            await asyncio.sleep(self.config.retry_delay * (2**attempt))
        except CaptchaError: raise
        except Exception as exc: logger.error("Unexpected error in solver %s: %s", self.name, exc, exc_info=True)
        return None
    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    async def close(self) -> None:
        if self._session is not None: await self._session.close()

class ChainedCaptchaSolver(CaptchaSolver):
    def __init__(self, solvers: List[CaptchaSolver], config: CaptchaConfig, session: Optional[aiohttp.ClientSession] = None) -> None:
        super().__init__("chain", config, session)
        self.solvers = solvers
    async def health_check(self) -> bool:
        for solver in self.solvers:
            if await solver.health_check(): return True
        return False
    def estimate_cost(self, _captcha_type: CaptchaType) -> float: return min(s.estimate_cost(_captcha_type) for s in self.solvers)
    async def _solve_impl(self, site_key: str, url: str, captcha_type: CaptchaType, **kwargs: Any) -> CaptchaSolveResult:
        last_error = None
        for solver in self.solvers:
            try:
                result = await solver.solve(site_key, url, captcha_type, **kwargs)
                if result.success: return result
                last_error = result.error
            except CaptchaError as e:
                last_error = str(e)
                logger.warning("Solver %s failed: %s", solver.name, e)
                continue
        return CaptchaSolveResult(error=f"All solvers failed. Last error: {last_error}")
