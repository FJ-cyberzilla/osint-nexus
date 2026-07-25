from typing import Optional, List, Dict, Any
import aiohttp
from osint_nexus.core.captcha.base import CaptchaSolver, CaptchaConfig, CaptchaSolveResult, CaptchaType, CaptchaError
from osint_nexus.core.captcha.solvers.two_captcha import TwoCaptchaSolver
from osint_nexus.core.captcha.solvers.anti_captcha import AntiCaptchaSolver

class CaptchaSolverRegistry:
    """Registry with priority ordering and dynamic selection."""

    def __init__(self, config: CaptchaConfig) -> None:
        self.config = config
        self._solvers: Dict[str, CaptchaSolver] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    def register(self, solver: CaptchaSolver) -> None:
        """Register a solver instance."""
        self._solvers[solver.name] = solver

    def unregister(self, name: str) -> None:
        """Remove a solver."""
        self._solvers.pop(name, None)

    def get_solver(self, name: str) -> Optional[CaptchaSolver]:
        """Return a solver by name."""
        return self._solvers.get(name)

    def list_solvers(self) -> List[str]:
        """Return a list of registered solver names."""
        return list(self._solvers.keys())

    async def get_preferred_solver(
        self, captcha_type: CaptchaType
    ) -> Optional[CaptchaSolver]:
        """Return the highest‑priority solver that supports the type."""
        for name in self.config.solver_priority:
            solver = self._solvers.get(name)
            if solver and await solver.health_check():
                return solver
        # Fallback to any solver
        for solver in self._solvers.values():
            if await solver.health_check():
                return solver
        return None

    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        preferred_solver: Optional[str] = None,
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
        self, captcha_type: CaptchaType, preferred_solver: Optional[str]
    ) -> Optional[CaptchaSolver]:
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

from osint_nexus.core.captcha.base import ChainedCaptchaSolver
from osint_nexus.core.config import get_config

async def create_captcha_registry(
    config: Optional[CaptchaConfig] = None,
    session: Optional[aiohttp.ClientSession] = None,
) -> CaptchaSolverRegistry:
    """
    Create a fully configured registry with all enabled solvers.
    """
    if config is None:
        main_config = get_config()
        config = CaptchaConfig.from_config(main_config)

    registry = CaptchaSolverRegistry(config)

    solvers_to_add = []

    # 2Captcha
    if config.two_captcha_key:
        solvers_to_add.append(TwoCaptchaSolver(config, session))

    # Anti-Captcha
    if config.anti_captcha_key:
        solvers_to_add.append(AntiCaptchaSolver(config, session))

    # If more than one solver, add a chain solver as well
    if len(solvers_to_add) > 1:
        chain = ChainedCaptchaSolver(solvers_to_add, config, session)
        registry.register(chain)

    for solver in solvers_to_add:
        registry.register(solver)

    return registry
