from typing import Any

import aiohttp

from osint_nexus.core.captcha.base import (
    CaptchaConfig,
    CaptchaError,
    CaptchaSolver,
    CaptchaSolveResult,
    CaptchaType,
)
from osint_nexus.core.captcha.chained import ChainedCaptchaSolver
from osint_nexus.core.captcha.solvers.anti_captcha import AntiCaptchaSolver
from osint_nexus.core.captcha.solvers.two_captcha import TwoCaptchaSolver
from osint_nexus.core.config import get_config
from osint_nexus.core.db.cache_repository import CacheRepository


class CaptchaSolverRegistry:
    """Registry with priority ordering and dynamic selection."""

    def __init__(self, config: CaptchaConfig, cache_repository: CacheRepository | None = None) -> None:
        self.config = config
        self.cache_repository = cache_repository
        self._solvers: dict[str, CaptchaSolver] = {}
        self._session: aiohttp.ClientSession | None = None

    def register(self, solver: CaptchaSolver) -> None:
        """Register a solver instance."""
        self._solvers[solver.name] = solver

    def unregister(self, name: str) -> None:
        """Remove a solver."""
        self._solvers.pop(name, None)

    def get_solver(self, name: str) -> CaptchaSolver | None:
        """Return a solver by name."""
        return self._solvers.get(name)

    def list_solvers(self) -> list[str]:
        """Return a list of registered solver names."""
        return list(self._solvers.keys())

    async def _check_solvers_in_list(self, solver_names: list[str]) -> CaptchaSolver | None:
        """Check a list of solvers and return the first healthy one."""
        for name in solver_names:
            solver = self._solvers.get(name)
            if solver and await solver.health_check():
                return solver
        return None

    async def get_preferred_solver(self, captcha_type: CaptchaType) -> CaptchaSolver | None:
        """Return the highest‑priority solver that supports the type."""
        # 1. Try preferred solvers
        solver = await self._check_solvers_in_list(self.config.solver_priority)
        if solver:
            return solver

        # 2. Fallback to any healthy solver
        return await self._check_solvers_in_list(list(self._solvers.keys()))

    async def _get_cached_solution(self, cache_key: str) -> CaptchaSolveResult | None:
        """Returns cached result if available."""
        if self.cache_repository:
            cached = await self.cache_repository.get(cache_key)
            if cached and "token" in cached:
                return CaptchaSolveResult(token=cached["token"], cost=0.0, solver_name="cache")
        return None

    async def _perform_solve(
        self,
        solver: CaptchaSolver,
        site_key: str,
        url: str,
        captcha_type: CaptchaType,
        cache_key: str,
        **kwargs: Any,
    ) -> CaptchaSolveResult:
        """Performs the actual solving and handles caching."""
        try:
            result = await solver.solve(site_key, url, captcha_type, **kwargs)
            if result.success and self.cache_repository:
                await self.cache_repository.set(cache_key, result.token)
            return result
        except CaptchaError as e:
            return CaptchaSolveResult(error=str(e))

    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        preferred_solver: str | None = None,
        **kwargs: Any,
    ) -> CaptchaSolveResult:
        """
        Solve using preferred solver or auto‑select the best available.
        """
        cache_key = f"{site_key}:{url}"
        cached = await self._get_cached_solution(cache_key)
        if cached:
            return cached

        solver = await self._select_solver(captcha_type, preferred_solver)
        if solver is None:
            return CaptchaSolveResult(error="No healthy solver available")

        return await self._perform_solve(solver, site_key, url, captcha_type, cache_key, **kwargs)

    async def _select_solver(
        self, captcha_type: CaptchaType, preferred_solver: str | None
    ) -> CaptchaSolver | None:
        """Select a suitable solver."""
        if preferred_solver:
            solver = self._solvers.get(preferred_solver)
            if solver and await solver.health_check():
                return solver
            # logger.warning("Preferred solver %s is unhealthy or missing", preferred_solver)

        return await self.get_preferred_solver(captcha_type)

    async def close(self) -> None:
        """Close all solvers' sessions."""
        for solver in self._solvers.values():
            await solver.close()
        if self._session:
            await self._session.close()


def _instantiate_solvers(
    config: CaptchaConfig,
    session: aiohttp.ClientSession | None,
    solver_configs: dict[str, Any] | None,
) -> list[CaptchaSolver]:
    """Instantiate configured solvers."""
    solvers: list[CaptchaSolver] = []

    # Define solver mapping: name -> (constructor, config_key_value)
    mapping = {
        "two_captcha": (TwoCaptchaSolver, config.two_captcha_key),
        "anti_captcha": (AntiCaptchaSolver, config.anti_captcha_key),
    }

    for name, (cls, key) in mapping.items():
        if solver_configs:
            if name in solver_configs:
                solvers.append(cls(config, session))
        elif key:
            solvers.append(cls(config, session))

    return solvers


async def create_captcha_registry(
    config: CaptchaConfig | None = None,
    session: aiohttp.ClientSession | None = None,
    solver_configs: dict[str, Any] | None = None,
) -> CaptchaSolverRegistry:
    """
    Create a fully configured registry with all enabled solvers.
    """
    if config is None:
        main_config = get_config()
        config = CaptchaConfig.from_config(main_config)

    registry = CaptchaSolverRegistry(config)
    solvers_to_add = _instantiate_solvers(config, session, solver_configs)

    # If more than one solver, add a chain solver as well
    if len(solvers_to_add) > 1:
        chain = ChainedCaptchaSolver(solvers_to_add, config, session)
        registry.register(chain)

    for solver in solvers_to_add:
        registry.register(solver)

    return registry
