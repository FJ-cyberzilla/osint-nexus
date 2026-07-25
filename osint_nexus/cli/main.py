"""
Command Line Interface entry point for OSINT Nexus.

Provides a Rich-powered interactive UI with real-time status updates,
concurrency-safe signal handling, and professional report generation.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.logging import RichHandler
from osint_nexus.core.config import LOG_FILE_PATH

from osint_nexus.core import constants
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.utils.security import SecurityUtility
from osint_nexus.utils.troubleshoot import (
    inspect_database_schema,
    print_latest_scan_results,
    run_health_check,
    setup_logging,
)

# Global UI components
console = Console()
logger = logging.getLogger("osint_nexus.cli")


def get_layout(progress: Progress, username: str, status_line: str, results_table: Table) -> Layout:
    """Creates the overall TUI layout."""
    layout = Layout()
    layout.split_column(
        Layout(
            Panel(
                f"[bold orange]OSINT Nexus Reconnaissance v{constants.VERSION}[/]\n"
                f"[dim]Target:[/] [bold cyan]{username}[/]",
                border_style=constants.COLOR_ORANGE,
            ),
            size=4,
        ),
        Layout(progress, size=3),
        Layout(
            Panel(
                f"[dim]Current Action:[/] [bold orange]{status_line}[/]",
                border_style="dim",
            ),
            size=3,
        ),
        Layout(results_table),
    )
    return layout


def _setup_signals(agent: OSINTAgent) -> None:
    """Registers signal handlers for graceful shutdown."""

    def handle_signal(*_args: Any) -> None:
        console.print("\n[bold red]Interrupt received! Aborting scans gracefully...[/]")
        if hasattr(agent, "orchestrator"):
            agent.orchestrator.abort()
        elif hasattr(agent, "abort_scan"):
            agent.abort_scan()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            signal.signal(sig, handle_signal)


def _format_intel_row(intel: Any) -> tuple[str, str, str]:
    """Formats an IntelligenceObject into UI row components."""
    error = intel.metadata.get("error")

    if error:
        status = "[bold red]Error[/]"
        conf_str = "-"
        details = error
    elif intel.found:
        status = "[bold green]Match Found[/]"
        conf_str = f"[green]{intel.confidence * 100:.0f}%[/]"
        device_data = intel.metadata.get("device_inference", {})
        if device_data and device_data.get("device_type") != "Unknown":
            dev_type = device_data.get("device_type")
            os_guess = device_data.get("os_guess")
            details = f"[white]Device:[/] {dev_type} ({os_guess})"
        else:
            details = "Identity confirmed"
    else:
        status = "[dim]Not Found[/]"
        conf_str = "-"
        details = "No associated footprint"

    return status, conf_str, details


async def async_main(args: argparse.Namespace) -> None:
    """Main async entry point for the CLI."""
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    safe_username = SecurityUtility.sanitize_input(args.username)
    agent = OSINTAgent(safe_username)
    _setup_signals(agent)

    providers = agent.subsystems.registry.get_providers()
    total_providers = len(providers)

    if total_providers == 0:
        console.print("[bold red]Fatal:[/] No providers registered in the system.")
        return

    progress, task = _initialize_progress(total_providers)
    table = _initialize_results_table()
    status_text = "Initializing subsystems..."

    try:
        with Live(
            get_layout(progress, safe_username, status_text, table), console=console, refresh_per_second=10
        ) as live:
            await _run_scan_loop(agent, live, progress, task, table, safe_username, status_text, args)

    except asyncio.CancelledError:
        console.print("[yellow]Scan cancelled by system.[/]")

    _generate_report(agent)


def _initialize_progress(total: int) -> tuple[Progress, Any]:
    progress = Progress(
        SpinnerColumn(style="bold orange1"),
        TextColumn("[bold orange1]{task.description}"),
        BarColumn(bar_width=40, complete_style="bold orange1", finished_style="green"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    task = progress.add_task("[bold orange1]Executing intelligence gather...", total=total)
    return progress, task


def _initialize_results_table() -> Table:
    table = Table(
        title="[bold orange]Active Reconnaissance Results[/]",
        border_style=constants.COLOR_ORANGE,
        header_style="bold white",
        expand=True,
    )
    table.add_column("Provider", style="cyan", width=20)
    table.add_column("Status", width=15)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Details", style="dim")
    return table


async def _run_scan_loop(
    agent: OSINTAgent,
    live: Live,
    progress: Progress,
    task: Any,
    table: Table,
    username: str,
    status_text: str,
    args: argparse.Namespace,
) -> None:
    async for intel in agent.run_scan(username=username, timeout=args.timeout):
        status, conf_str, details = _format_intel_row(intel)
        table.add_row(intel.platform, status, conf_str, details)

        has_error = "error" in intel.metadata
        status_text = (
            f"Analyzed {intel.platform} -> "
            f"{'Match' if intel.found else ('Error' if has_error else 'Clear')}"
        )
        progress.update(task, advance=1)
        live.update(get_layout(progress, username, status_text, table))


def _generate_report(agent: OSINTAgent) -> None:
    input("\n[bold orange1]Scan complete. Press Enter to generate final report...[/]")
    console.print(
        Panel(
            "[bold white]Reconnaissance Complete![/]\n[orange1]Compiling intelligence report...[/]",
            border_style="green",
        )
    )

    try:
        report_content = agent.get_final_report()
        console.print(
            Panel(
                report_content,
                border_style=constants.COLOR_ORANGE,
                title="[bold white]OSINT Nexus Final Report[/]",
                padding=(1, 2),
            )
        )
    except Exception as e:
        logger.error("Failed to generate final report: %s", e)
        console.print(f"[bold red]Error generating final report:[/] {e}")


def main() -> None:
    """Synchronous entry point that safely wraps the asyncio loop."""
    parser = argparse.ArgumentParser(description="Advanced OSINT Target Scanner")
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

    # Scanner command
    scan_parser = subparsers.add_parser("scan", help="Scan a target username")
    scan_parser.add_argument("--username", required=True, help="Target username to investigate")
    scan_parser.add_argument("--timeout", type=float, default=15.0, help="Per-provider timeout in seconds")
    scan_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Health command
    subparsers.add_parser("health", help="Check provider health status")

    # DB-info command
    subparsers.add_parser("db-info", help="Inspect database schema and records")

    args = parser.parse_args()

    setup_logging(verbose=args.debug)

    if args.command == "health":
        run_health_check()
        return
    elif args.command == "db-info":
        inspect_database_schema()
        print_latest_scan_results()
        return

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        console.print("\n[bold red]Execution forcefully terminated by user.[/]")
        sys.exit(130)


if __name__ == "__main__":
    main()
