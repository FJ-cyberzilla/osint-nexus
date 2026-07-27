from typing import Any

import aiohttp

from osint_nexus.core.captcha.base import (
    CaptchaConfig,
    CaptchaError,
    CaptchaSolver,
    CaptchaSolveResult,
    CaptchaType,
    ChainedCaptchaSolver,
)
from osint_nexus.core.captcha.solvers.anti_captcha import AntiCaptchaSolver
from osint_nexus.core.captcha.solvers.two_captcha import TwoCaptchaSolver
from osint_nexus.core.config import get_config


class CaptchaSolverRegistry:
    """Registry with priority ordering and dynamic selection."""

    def __init__(self, config: CaptchaConfig) -> None:
        self.config = config
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
        solver = await self._select_solver(captcha_type, preferred_solver)

        if solver is None:
            return CaptchaSolveResult(error="No healthy solver available")

        try:
            return await solver.solve(site_key, url, captcha_type, **kwargs)
        except CaptchaError as e:
            return CaptchaSolveResult(error=str(e))

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
    solvers = []
    if solver_configs:
        if "two_captcha" in solver_configs:
            solvers.append(TwoCaptchaSolver(config, session))
        if "anti_captcha" in solver_configs:
            solvers.append(AntiCaptchaSolver(config, session))
    else:
        # Fallback to existing logic if no specific solver_configs provided
        if config.two_captcha_key:
            solvers.append(TwoCaptchaSolver(config, session))
        if config.anti_captcha_key:
            solvers.append(AntiCaptchaSolver(config, session))
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
