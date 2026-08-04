import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Mock dependencies that cause circular imports
sys.modules["osint_nexus.core"] = MagicMock()
# Mock Config directly, instead of using MagicMock(spec=Config) because Config is mocked
config_mock = MagicMock()
sys.modules["osint_nexus.core.config"] = MagicMock(Config=config_mock)

from osint_nexus.utils.retry import RetryHandler  # noqa: E402


@pytest.fixture
def mock_config() -> MagicMock:
    config = MagicMock()
    config.retry_attempts = 3
    config.retry_backoff_factor = 0.1
    return config


@pytest.mark.asyncio
async def test_retry_handler_success(mock_config: MagicMock) -> None:
    handler = RetryHandler(mock_config)
    func = AsyncMock(return_value="success")

    result = await handler.run(func)
    assert result == "success"
    assert func.call_count == 1


@pytest.mark.asyncio
async def test_retry_handler_retry_success(mock_config: MagicMock) -> None:
    handler = RetryHandler(mock_config)
    func = AsyncMock(side_effect=[Exception("fail"), "success"])

    result = await handler.run(func)
    assert result == "success"
    assert func.call_count == 2


@pytest.mark.asyncio
async def test_retry_handler_exhausted(mock_config: MagicMock) -> None:
    handler = RetryHandler(mock_config)
    func = AsyncMock(side_effect=Exception("fail"))

    with pytest.raises(Exception, match="fail"):
        await handler.run(func)
    assert func.call_count == 3


@pytest.mark.asyncio
async def test_retry_handler_health_check() -> None:
    handler = RetryHandler(MagicMock())
    assert await handler.health_check() is True
