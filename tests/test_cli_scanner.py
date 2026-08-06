from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from osint_nexus.cli.scanner import generate_report, run_scan
from osint_nexus.core.exceptions import NexusError


@pytest.mark.asyncio
async def test_run_scan_no_providers():
    mock_agent = MagicMock()
    mock_agent.subsystems.registry.get_providers.return_value = []

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        await run_scan(mock_agent, "testuser", 30.0)
        mock_console.print.assert_any_call("[bold red]Fatal:[/] No providers registered in the system.")


@pytest.mark.asyncio
async def test_run_scan_success():
    mock_agent = MagicMock()
    mock_agent.subsystems.registry.get_providers.return_value = ["p1"]

    with patch("osint_nexus.cli.scanner.OSINTApp") as mock_app_class:
        mock_app = AsyncMock()
        mock_app_class.return_value = mock_app

        with patch("osint_nexus.cli.scanner.console") as mock_console:
            await run_scan(mock_agent, "testuser", 30.0)

            mock_app.run_async.assert_awaited_once()
            mock_console.print.assert_any_call("\n[bold green]Scan completed successfully![/]")


def test_generate_report_success():
    mock_agent = MagicMock()
    mock_agent.get_final_report.return_value = "Report content"

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        generate_report(mock_agent)
        mock_console.print.assert_any_call(
            ANY  # The Panel object
        )
        mock_agent.get_final_report.assert_called_once()


def test_generate_report_attribute_error():
    mock_agent = MagicMock()
    del mock_agent.get_final_report  # Ensure AttributeError

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        generate_report(mock_agent)
        mock_console.print.assert_any_call("[yellow]Warning: Final report method not available.[/]")


def test_generate_report_nexus_error():
    mock_agent = MagicMock()
    mock_agent.get_final_report.side_effect = NexusError("Failure")

    with patch("osint_nexus.cli.scanner.console") as mock_console:
        generate_report(mock_agent)
        mock_console.print.assert_any_call("[bold red]Error generating final report:[/] Failure")
