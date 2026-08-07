from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner

from osint_nexus.cli.ui import (
    OSINTApp,
)
from osint_nexus.core import constants
from osint_nexus.core.agent import OSINTAgent

console = Console()


async def run_scan(
    agent: OSINTAgent,
    username: str,
    timeout: float,
) -> None:
    """Execute the scan and drive the TUI."""
    # Get provider list from agent
    providers = agent.subsystems.registry.get_providers()
    total = len(providers)
    if total == 0:
        console.print("[bold red]Fatal:[/] No providers registered in the system.")
        return

    # Run TUI
    app = OSINTApp(agent, username, total, timeout)
    await app.run_async()


async def generate_report(agent: OSINTAgent) -> None:
    """Generate and display the final report with a real-time progress indicator."""

    # Spinner for report compilation
    spinner = Spinner("dots", text="[orange1]Compiling intelligence report...[/]")

    with Live(spinner, refresh_per_second=10, console=console):
        try:
            report_content = await agent.get_final_report()
        except Exception as e:
            console.print(f"[bold red]Error generating final report:[/] {e}")
            return

    # Display the actual report
    console.print(
        Panel(
            report_content,
            border_style=constants.COLOR_ORANGE,
            title="[bold white]OSINT Nexus Final Report[/]",
            padding=(1, 2),
        )
    )
