from unittest.mock import AsyncMock, MagicMock

import pytest

from osint_nexus.core.captcha.base import CaptchaConfig, CaptchaSolver, CaptchaType
from osint_nexus.core.captcha.registry import CaptchaSolverRegistry


@pytest.fixture
def mock_config() -> MagicMock:
    config = MagicMock(spec=CaptchaConfig)
    config.solver_priority = ["solver1", "solver2"]
    return config


@pytest.fixture
def registry(mock_config: MagicMock) -> CaptchaSolverRegistry:
    return CaptchaSolverRegistry(mock_config)


def test_registry_registration(registry: CaptchaSolverRegistry) -> None:
    solver = MagicMock(spec=CaptchaSolver)
    solver.name = "solver1"

    registry.register(solver)
    assert registry.get_solver("solver1") == solver
    assert "solver1" in registry.list_solvers()

    registry.unregister("solver1")
    assert registry.get_solver("solver1") is None


@pytest.mark.asyncio
async def test_get_preferred_solver(registry: CaptchaSolverRegistry) -> None:
    solver1 = AsyncMock(spec=CaptchaSolver)
    solver1.name = "solver1"
    solver1.health_check.return_value = False

    solver2 = AsyncMock(spec=CaptchaSolver)
    solver2.name = "solver2"
    solver2.health_check.return_value = True

    registry.register(solver1)
    registry.register(solver2)

    # Priority is ["solver1", "solver2"]
    # solver1 is unhealthy, so should return solver2
    solver = await registry.get_preferred_solver(CaptchaType.RECAPTCHA_V2)
    assert solver == solver2


@pytest.mark.asyncio
async def test_solve_failure(registry: CaptchaSolverRegistry) -> None:
    # No solvers registered
    result = await registry.solve("site_key", "url")
    assert result.error == "No healthy solver available"


@pytest.mark.asyncio
async def test_solve_exception(registry: CaptchaSolverRegistry) -> None:
    solver = AsyncMock(spec=CaptchaSolver)
    solver.name = "solver1"
    solver.health_check.return_value = True

    from osint_nexus.core.captcha.base import CaptchaError

    solver.solve.side_effect = CaptchaError("solver error")

    registry.register(solver)

    result = await registry.solve("site_key", "url", preferred_solver="solver1")
    assert result.error == "solver error"


@pytest.mark.asyncio
async def test_close(registry: CaptchaSolverRegistry) -> None:
    solver1 = AsyncMock(spec=CaptchaSolver)
    solver1.name = "solver1"

    registry.register(solver1)
    await registry.close()

    solver1.close.assert_called_once()


@pytest.mark.asyncio
async def test_instantiate_solvers() -> None:
    from osint_nexus.core.captcha.base import CaptchaConfig
    from osint_nexus.core.captcha.registry import _instantiate_solvers

    config = MagicMock(spec=CaptchaConfig)
    config.two_captcha_key = "key1"
    config.anti_captcha_key = None

    solvers = _instantiate_solvers(config, None, None)
    assert len(solvers) == 1
    assert solvers[0].__class__.__name__ == "TwoCaptchaSolver"


@pytest.mark.asyncio
async def test_create_captcha_registry() -> None:
    from unittest.mock import patch

    from osint_nexus.core.captcha.registry import create_captcha_registry

    with patch("osint_nexus.core.captcha.registry._instantiate_solvers") as mock_instantiate:
        solver = MagicMock(spec=CaptchaSolver)
        solver.name = "solver1"
        mock_instantiate.return_value = [solver]

        registry = await create_captcha_registry()
        assert registry.get_solver("solver1") == solver
