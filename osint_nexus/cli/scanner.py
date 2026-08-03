from rich.console import Console
from rich.live import Live
from rich.panel import Panel

# Assuming UI components remain in cli/main.py, I might need to move them too.
# For simplicity, move UI components here or into a separate 'cli/ui.py'.
# Let's move UI components here.
from osint_nexus.cli.ui import (
    CLIController,
    setup_signals,
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

    controller = CLIController(username, total)
    setup_signals(agent)

    # Prepare live display
    with Live(
        controller.get_layout(console.width),
        console=console,
        refresh_per_second=10,
    ) as live:
        # Iterate over the asynchronous generator
        async for intel in agent.run_scan(username=username, timeout=timeout):
            controller.add_result(intel)
            live.update(controller.get_layout(console.width))

        # Ensure progress reaches total (in case some providers were skipped)
        remaining = total - controller.progress.tasks[controller.task].completed
        if remaining > 0:
            controller.progress.update(controller.task, advance=remaining)
            live.update(controller.get_layout(console.width))

        # Display final summary
        console.print("\n[bold green]Scan completed successfully![/]")
        console.print("[bold green]Reconnaissance finished.[/]")


def generate_report(agent: OSINTAgent) -> None:
    """Generate and display the final report."""
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
    except AttributeError:
        console.print("[yellow]Warning: Final report method not available.[/]")
    except Exception as e:
        # logger.error("Failed to generate final report: %s", e)
        console.print(f"[bold red]Error generating final report:[/] {e}")
