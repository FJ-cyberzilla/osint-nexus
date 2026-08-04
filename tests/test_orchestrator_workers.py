import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.orchestrator.workers import ProviderWorker


@pytest.fixture
def mock_deps() -> MagicMock:
    deps = MagicMock()
    deps.health = MagicMock()
    return deps


@pytest.fixture
def mock_runner() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_provider() -> MagicMock:
    provider = MagicMock()
    provider.name = "test_provider"
    return provider


@pytest.mark.asyncio
async def test_provider_worker_execute_success(
    mock_deps: MagicMock, mock_runner: AsyncMock, mock_provider: MagicMock
) -> None:
    worker = ProviderWorker(mock_deps, mock_runner)
    abort_event = asyncio.Event()

    expected_intel = IntelligenceObject(
        platform="test_provider", username="user", found=True, dork="dork", confidence=1.0
    )
    mock_runner.run.return_value = expected_intel

    intel = await worker.execute(mock_provider, "user", abort_event)

    assert intel == expected_intel
    mock_deps.health.record_success.assert_called_with("test_provider")


@pytest.mark.asyncio
async def test_provider_worker_execute_aborted(
    mock_deps: MagicMock, mock_runner: AsyncMock, mock_provider: MagicMock
) -> None:
    worker = ProviderWorker(mock_deps, mock_runner)
    abort_event = asyncio.Event()
    abort_event.set()

    intel = await worker.execute(mock_provider, "user", abort_event)

    assert intel.found is False
    assert intel.metadata["error"] == "Scan aborted"


@pytest.mark.asyncio
async def test_provider_worker_execute_failure(
    mock_deps: MagicMock, mock_runner: AsyncMock, mock_provider: MagicMock
) -> None:
    worker = ProviderWorker(mock_deps, mock_runner)
    abort_event = asyncio.Event()

    mock_runner.run.side_effect = Exception("failed")

    intel = await worker.execute(mock_provider, "user", abort_event)

    assert intel.found is False
    assert "ProviderError" in intel.metadata["error"]
    mock_deps.health.record_failure.assert_called_with("test_provider")
