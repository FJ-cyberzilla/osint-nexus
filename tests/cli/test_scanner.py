from unittest.mock import ANY, AsyncMock, MagicMock, create_autospec, patch

import pytest

from osint_nexus.cli.scanner import generate_report, run_scan
from osint_nexus.cli.ui import ScanConfig
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.exceptions import NexusError


@pytest.mark.asyncio
async def test_run_scan_no_providers():
    mock_agent = MagicMock()
    mock_agent.__class__ = OSINTAgent
    mock_agent.subsystems = MagicMock()
    mock_agent.subsystems.registry.get_providers.return_value = []
    
    config = ScanConfig(agent=mock_agent, username="testuser", total=10, timeout=30.0)

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        await run_scan(config)
        mock_console.print.assert_any_call("[bold red]Fatal:[/] No providers registered in the system.")


@pytest.mark.asyncio
async def test_run_scan_success():
    mock_agent = MagicMock()
    mock_agent.__class__ = OSINTAgent
    mock_agent.subsystems = MagicMock()
    mock_agent.subsystems.registry.get_providers.return_value = ["p1"]
    
    config = ScanConfig(agent=mock_agent, username="testuser", total=10, timeout=30.0)

    with patch("osint_nexus.cli.scanner.OSINTApp", autospec=True) as mock_app_class:
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app

        with patch("osint_nexus.cli.scanner.console") as mock_console:
            await run_scan(config)

            mock_app.run_async.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_report_success():
    mock_agent = MagicMock()
    mock_agent.__class__ = OSINTAgent
    mock_agent.get_final_report = AsyncMock(return_value="Report content")

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        await generate_report(mock_agent)
        mock_console.print.assert_any_call(
            ANY  # The Panel object
        )
        mock_agent.get_final_report.assert_called_once()


@pytest.mark.asyncio
async def test_generate_report_attribute_error():
    mock_agent = create_autospec(OSINTAgent, instance=True)
    # If the method doesn't exist, we need to mock it as a coroutine that raises AttributeError when called
    mock_agent.get_final_report = AsyncMock(side_effect=AttributeError("Method not available"))

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        await generate_report(mock_agent)
        # Note: The actual code checks 'except Exception as e', so Attribute Error will be caught and printed as a general error
        # Adjusting test expectation to match implementation
        mock_console.print.assert_any_call("[bold red]Error generating final report:[/] Method not available")


@pytest.mark.asyncio
async def test_generate_report_nexus_error():
    mock_agent = create_autospec(OSINTAgent, instance=True)
    mock_agent.get_final_report = AsyncMock(side_effect=NexusError("Failure"))

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        await generate_report(mock_agent)
        mock_console.print.assert_any_call("[bold red]Error generating final report:[/] Failure")
