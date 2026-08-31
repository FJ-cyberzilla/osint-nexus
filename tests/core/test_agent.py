from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.intelligence import IntelligenceObject


@pytest.fixture
def mock_subsystems():
    """Mock external dependency subsystems to isolate OSINTAgent behavior."""
    with (
        patch("osint_nexus.core.agent.Config"),
        patch("osint_nexus.core.agent.DatabaseManager") as mock_db,
        patch("osint_nexus.core.agent.BrowserPoolManager") as mock_browser,
        patch("osint_nexus.core.agent.NetworkManager") as mock_network,
        patch("osint_nexus.core.agent.ProviderRegistry") as mock_registry,
        patch("osint_nexus.core.agent.ScanOrchestrator") as mock_orchestrator,
        patch("osint_nexus.core.agent.AdvancedReportGenerator") as mock_report,
    ):
        # Configure async mocks on resources needing cleanup
        mock_db_inst = mock_db.return_value
        mock_db_inst.ensure_initialized = AsyncMock()
        mock_db_inst.close = AsyncMock()

        mock_browser_inst = mock_browser.return_value
        mock_browser_inst.close = AsyncMock()

        mock_network_inst = mock_network.return_value
        mock_network_inst.close = AsyncMock()

        mock_report_inst = mock_report.return_value
        mock_report_inst.generate = AsyncMock()

        yield {
            "db": mock_db_inst,
            "browser": mock_browser_inst,
            "network": mock_network_inst,
            "registry": mock_registry.return_value,
            "orchestrator": mock_orchestrator.return_value,
            "report": mock_report_inst,
        }


def test_agent_initialization(mock_subsystems):
    """Verify that OSINTAgent binds state correctly on init."""
    target_user = "test_target"
    ja3 = "771,4865-4866-4867,0-23-65281,29-23-24,0"

    agent = OSINTAgent(username=target_user, ja3_hash=ja3)

    assert agent.username == target_user
    assert agent.orchestrator == mock_subsystems["orchestrator"]


@pytest.mark.asyncio
async def test_async_context_manager_lifecycle(mock_subsystems):
    """Verify entering and exiting the context manager triggers initialization and cleanup."""
    agent = OSINTAgent(username="test_user")

    async with agent as active_agent:
        assert active_agent is agent
        mock_subsystems["db"].ensure_initialized.assert_awaited_once()

    # Verify resource teardown on context exit
    mock_subsystems["network"].close.assert_awaited_once()
    mock_subsystems["browser"].close.assert_awaited_once()
    mock_subsystems["db"].close.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_scan_yields_intelligence_objects(mock_subsystems):
    """Ensure run_scan delegates to orchestrator using instance username and yields results."""
    mock_intel_1 = MagicMock(spec=IntelligenceObject)
    mock_intel_2 = MagicMock(spec=IntelligenceObject)

    # Set up generator mock for orchestrator
    async def mock_generator(*args, **kwargs):
        yield mock_intel_1
        yield mock_intel_2

    mock_subsystems["orchestrator"].run_scan.side_effect = mock_generator
    mock_subsystems["registry"].get_providers.return_value = ["provider1", "provider2"]

    agent = OSINTAgent(username="target_user")

    results = []
    async for intel in agent.run_scan(timeout=10.0):
        results.append(intel)

    assert results == [mock_intel_1, mock_intel_2]
    mock_subsystems["orchestrator"].run_scan.assert_called_once_with(
        "target_user", ["provider1", "provider2"], timeout=10.0
    )


@pytest.mark.asyncio
async def test_get_final_report(mock_subsystems):
    """Verify report generation passes bound target username to report generator."""
    mock_panel = MagicMock()
    mock_subsystems["report"].generate.return_value = mock_panel

    agent = OSINTAgent(username="report_user")
    report = await agent.get_final_report()

    assert report is mock_panel
    mock_subsystems["report"].generate.assert_awaited_once_with("report_user")


def test_abort_scan_delegates_to_orchestrator(mock_subsystems):
    """Verify abort_scan triggers orchestrator abort."""
    agent = OSINTAgent(username="abort_user")
    agent.abort_scan()

    mock_subsystems["orchestrator"].abort.assert_called_once()
