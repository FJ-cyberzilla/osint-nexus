"""
Command‑line interface for OSINT Nexus.

Provides an interactive, rich‑console experience for scanning a username
across all registered providers. Displays real-time updates, structured
Pydantic data integration, and professional UI elements.
"""
from __future__ import annotations

import asyncio
import argparse
import logging
import signal
import sys
import time
from typing import List, Tuple, Any

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.layout import Layout

from osint_nexus.core import constants
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.health import HealthTracker
from osint_nexus.utils.security import SecurityUtility

# Configure Rich Console
console = Console(theme=Theme({"orange": constants.COLOR_ORANGE}), force_terminal=True)
logger = logging.getLogger("osint_nexus.cli")

# Shared singleton for HealthTracker
_health_tracker = HealthTracker()

def run_health_check() -> None:
    """Displays the current health status of all providers."""
    table = Table(title="Provider Health Status", expand=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Status")
    table.add_column("Failures")
    table.add_column("Last Failure")

    # Access tracker instance directly
    providers = list(_health_tracker.platform_failures.keys())
    
    exit_code = 0
    
    for provider in providers:
        failures = _health_tracker.platform_failures.get(provider, 0)
        is_healthy = _health_tracker.is_healthy(provider)
        is_degraded = _health_tracker.is_degraded(provider)
        
        last_fail_ts = _health_tracker.last_failure_times.get(provider, 0.0)
        last_fail = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_fail_ts)) if last_fail_ts > 0 else "Never"
        
        if not is_healthy:
            status = "[bold red]CIRCUIT OPEN[/]"
            exit_code = 1
        elif is_degraded:
            status = "[bold yellow]DEGRADED[/]"
            exit_code = 1
        else:
            status = "[bold green]HEALTHY[/]"
            
        table.add_row(provider, status, str(failures), last_fail)
        
    console.print(table)
    sys.exit(exit_code)

def get_layout(
    progress: Progress,
    username: str,
    status_line: str,
    results_table: Table,
) -> Layout:
    """Builds the dynamic dashboard layout for the Live console."""
    layout = Layout()
    layout.split_column(
        Layout(
            Panel(
                f"[bold white]Target Identity:[/] [cyan]{username}[/]",
                border_style=constants.COLOR_ORANGE,
                title="[bold orange]OSINT Nexus Engine[/]",
                title_align="left"
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


def async_main(args: argparse.Namespace) -> None:
    """Main async entry point for the CLI."""
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    safe_username = SecurityUtility.sanitize_input(args.username)
    agent = OSINTAgent(safe_username)
    
    # Graceful shutdown handler
    def handle_signal(*_args: Any) -> None:
        console.print("\n[bold red]Interrupt received! Aborting scans gracefully...[/]")
        # Signal the orchestrator to cancel pending tasks and stop yielding
        if hasattr(agent, 'orchestrator'):
            agent.orchestrator.abort()
        elif hasattr(agent, 'abort_scan'):
            agent.abort_scan()
            
    # Cross-platform signal registration
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # Fallback for Windows
            signal.signal(sig, handle_signal)

    providers = agent.subsystems.registry.get_providers()
    total_providers = len(providers)
    
    if total_providers == 0:
        console.print("[bold red]Fatal:[/] No providers registered in the system.")
        return

    # UI Components setup
    progress = Progress(
        SpinnerColumn(style="orange"),
        TextColumn("[bold orange]{task.description}"),
        BarColumn(bar_width=40, complete_style="orange", finished_style="green"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    task = progress.add_task("[orange]Executing intelligence gather...", total=total_providers)

    table = Table(
        title="[bold orange]Active Reconnaissance Results[/]",
        border_style=constants.COLOR_ORANGE,
        header_style="bold white",
        expand=True
    )
    table.add_column("Provider", style="cyan", width=20)
    table.add_column("Status", width=15)
    table.add_column("Confidence", justify="right", width=12)
    table.add_column("Details", style="dim")

    status_text = "Initializing subsystems..."

    try:
        with Live(
            get_layout(progress, safe_username, status_text, table),
            console=console,
            refresh_per_second=10
        ) as live:
            
            # Consume the IntelligenceObject yielded by our new Orchestrator
            async for intel in agent.run_scan(username=safe_username, timeout=args.timeout):
                
                # Extract data from the new Pydantic structure
                provider_name = intel.platform
                error = intel.metadata.get("error")
                
                # Format UI based on results
                if error:
                    status = "[bold red]Error[/]"
                    conf_str = "-"
                    details = error
                elif intel.found:
                    status = "[bold green]Match Found[/]"
                    conf_str = f"[green]{intel.confidence * 100:.0f}%[/]"
                    
                    # Extract advanced metadata if available (like our new Device Inference)
                    device_data = intel.metadata.get("device_inference", {})
                    if device_data and device_data.get("device_type") != "Unknown":
                        dev_type = device_data.get('device_type')
                        os_guess = device_data.get('os_guess')
                        details = f"[white]Device:[/] {dev_type} ({os_guess})"
                    else:
                        details = "Identity confirmed"
                else:
                    status = "[dim]Not Found[/]"
                    conf_str = "-"
                    details = "No associated footprint"

                table.add_row(provider_name, status, conf_str, details)

                # Update Progress Bar
                status_text = f"Analyzed {provider_name} -> {'Match' if intel.found else ('Error' if error else 'Clear')}"
                progress.update(task, advance=1)
                live.update(get_layout(progress, safe_username, status_text, table))

    except asyncio.CancelledError:
        console.print("[yellow]Scan cancelled by system.[/]")
    
    # Wait for user input
    input("\n[bold orange]Scan complete. Press Enter to generate final report...[/]")

    # Prevent UI flickering at the end
    console.print(Panel(
        "[bold white]Reconnaissance Complete![/]\n[orange]Compiling intelligence report...[/]",
        border_style="green"
    ))

    # Output the Final Report (Leveraging the new ReportGenerator)
    try:
        report_content = agent.get_final_report()
        console.print(Panel(
            report_content,
            border_style=constants.COLOR_ORANGE,
            title="[bold white]OSINT Nexus Final Report[/]",
            padding=(1, 2)
        ))
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
    
    args = parser.parse_args()
    
    if args.command == "health":
        run_health_check()
        return

    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        # Failsafe for OSes where the signal handler doesn't catch it in time
        console.print("\n[bold red]Execution forcefully terminated by user.[/]")
        sys.exit(130)


if __name__ == "__main__":
    main()
