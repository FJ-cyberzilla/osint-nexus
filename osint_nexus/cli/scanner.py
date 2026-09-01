from typing import Protocol, runtime_checkable

from beartype import beartype
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner

from osint_nexus.cli.ui import OSINTApp, ScanConfig
from osint_nexus.core import constants
from osint_nexus.core.agent import OSINTAgent

console: Console = Console()


@runtime_checkable
class ProviderProtocol(Protocol):
    """Protocol interface replacing Any for registered OSINT providers."""

    name: str


@beartype
async def run_scan(config: ScanConfig) -> None:
    """Execute the scan and drive the TUI safely."""
    agent: OSINTAgent = config.agent
    providers: list[ProviderProtocol] = agent.subsystems.registry.get_providers()
    total: int = len(providers)

    if total == 0:
        console.print("[bold red]Fatal:[/] No providers registered in the system.")
        return

    config.total = total

    # Clean zero-comma single-argument call to OSINTApp
    app: OSINTApp = OSINTApp(config=config)
    await app.run_async()


@beartype
async def generate_report(agent: OSINTAgent) -> None:
    """Generate and display the final report with a real-time progress indicator."""
    spinner: Spinner = Spinner("dots", text="[orange1]Compiling intelligence report...[/]")

    try:
        with Live(renderable=spinner, refresh_per_second=10, console=console):
            report_content: str = await agent.get_final_report()

    except Exception as exc:
        console.print(f"[bold red]Error generating final report:[/] {exc}")
        return

    console.print(
        Panel(
            renderable=report_content,
            border_style=constants.COLOR_ORANGE,
            title="[bold white]OSINT Nexus Final Report[/]",
        )
    )
