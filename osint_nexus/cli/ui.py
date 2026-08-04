import asyncio
import signal
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import ProgressBar, RichLog

from osint_nexus.cli.widgets import (
    Header,
    IntelligenceDashboard,
    LogPanel,
    MetricsGraph,
    ReconProgress,
    ScanUpdate,
)
from osint_nexus.core.agent import OSINTAgent

console = Console()


class OSINTApp(App):
    """Main Textual application for OSINT Nexus."""

    CSS = """
    #main-container {
        layout: vertical;
    }
    Header {
        height: 3;
        border: solid cyan;
    }
    ReconProgress {
        height: 5;
        border: solid white;
    }
    IntelligenceDashboard {
        height: 100%;
        width: 100%;
    }
    MetricsGraph {
        width: 20;
    }
    LogPanel {
        height: 6;
        border: solid dim;
    }
    """

    def __init__(self, agent: OSINTAgent, username: str, total: int, timeout: float) -> None:
        super().__init__()
        self.agent = agent
        self.username = username
        self.total = total
        self.timeout = timeout

    def compose(self) -> ComposeResult:
        yield Container(
            Header(self.username, id="header"),
            ReconProgress(self.total, id="progress"),
            Horizontal(
                IntelligenceDashboard(id="dashboard"),
                MetricsGraph(id="metrics"),
            ),
            LogPanel(id="logs"),
            id="main-container",
        )

    def on_mount(self) -> None:
        """Start the scan worker."""
        self.run_worker(self.scan_worker(), exclusive=True)

    async def scan_worker(self) -> None:
        """Scanner worker."""
        async for intel in self.agent.run_scan(username=self.username, timeout=self.timeout):
            self.post_message(ScanUpdate(intel))

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        intel = message.intel
        self.query_one("#dashboard", IntelligenceDashboard).update_data(intel)
        # Update metrics, logs, etc.
        self.query_one("#progress", ReconProgress).query_one(ProgressBar).advance(1)
        self.query_one("#logs", LogPanel).query_one(RichLog).write(f"Analyzed {intel.platform}")


class HeaderComponent:
    """Renders the top branding and target info panel."""

    def __init__(self, username: str) -> None:
        self.username = username

    def render(self) -> Panel:
        return Panel(
            f"[bold cyan]OSINT Nexus[/] | [dim]Target:[/] [bold white]{self.username}[/]",
            border_style="cyan",
        )


class ProgressComponent:
    """Renders the real-time progress bar."""

    def __init__(self, progress: Progress, task: Any) -> None:
        self.progress = progress
        self.task = task

    def render(self) -> Panel:
        return Panel(self.progress, title="[bold white]Recon Progress[/]", border_style="white")


class DashboardComponent:
    """Renders the Intelligence Dashboard (Fingerprint, Footprint, etc.)."""

    def __init__(self) -> None:
        self.fingerprint = ""
        self.footprint = ""
        self.canvas = ""
        self.useragent = ""

    def update_data(self, intel: Any) -> None:
        """Extract and update intelligence data."""
        if not intel.found:
            return

        # Extract fingerprint (often platform-specific in metadata)
        self.fingerprint = intel.metadata.get("fingerprint", "Detected")

        # Extract footprint (metadata or platform specific)
        self.footprint = intel.metadata.get("footprint", "Active")

        # Canvas (using visuals if present)
        if intel.visuals and (intel.visuals.profile_picture or intel.visuals.banner_image):
            self.canvas = "Visuals Present"
        else:
            self.canvas = "Text/Data Only"

        # UserAgent (often platform specific metadata)
        self.useragent = intel.metadata.get("device_inference", {}).get("os_guess", "Generic")

    def render(self) -> Table:
        table = Table(title="Target Analysis", expand=True)
        table.add_column("Category")
        table.add_column("Details")
        table.add_row("Fingerprint", self.fingerprint)
        table.add_row("Footprint", self.footprint)
        table.add_row("Canvas", self.canvas)
        table.add_row("Useragent", self.useragent)
        return table


class LogComponent:
    """Renders the scrollable log/error panel."""

    def __init__(self) -> None:
        self.logs: list[str] = []

    def add_log(self, message: str) -> None:
        self.logs.append(message)

    def render(self) -> Panel:
        log_content = "\n".join(self.logs[-5:]) if self.logs else "[dim]No logs...[/]"
        return Panel(log_content, title="Live Logs", border_style="dim")


class MetricComponent:
    """Renders a simple ASCII success/failure metric graph."""

    def __init__(self) -> None:
        self.successes = 0
        self.failures = 0

    def update(self, intel: Any) -> None:
        if "error" in intel.metadata:
            self.failures += 1
        else:
            self.successes += 1

    def render(self) -> Panel:
        total = self.successes + self.failures
        if total == 0:
            graph = "No data yet."
        else:
            s_bar = "█" * (self.successes * 10 // total)
            f_bar = "░" * (self.failures * 10 // total)
            graph = f"{s_bar}{f_bar}"
        return Panel(graph, title="Success/Failure Trend", border_style="cyan")


class CLIController:
    """Manages the modular TUI components."""

    def __init__(self, username: str, total_providers: int) -> None:
        self.username = username
        self.total = total_providers
        self.progress, self.task = self._make_progress()

        # New Components
        self.header = HeaderComponent(username)
        self.progress_bar = ProgressComponent(self.progress, self.task)
        self.dashboard = DashboardComponent()
        self.logs = LogComponent()
        self.metrics = MetricComponent()

    def _make_progress(self) -> tuple[Progress, Any]:
        progress = Progress(
            SpinnerColumn(style="bold cyan"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console,
        )
        task = progress.add_task("Gathering intel...", total=self.total)
        return progress, task

    def get_layout(self, console_width: int) -> Layout:
        """Build the modular layout."""
        layout = Layout()
        layout.split_column(
            Layout(self.header.render(), size=3),
            Layout(self.progress_bar.render(), size=5),
            Layout(name="middle"),
            Layout(self.logs.render(), size=6),
        )

        # Split the middle layout into a row
        layout["middle"].split_row(
            Layout(self.dashboard.render()),
            Layout(self.metrics.render(), size=20),  # Adjusted size for better fit
        )
        return layout

    def add_result(self, intel: Any) -> None:
        """Update dashboard and logs with new intelligence."""
        # Update dashboard with new data
        self.dashboard.update_data(intel)
        self.metrics.update(intel)

        # Update logs
        status = "Found" if intel.found else "Not Found"
        self.logs.add_log(f"Analyzed {intel.platform}: {status}")

        # Update progress
        self.progress.update(self.task, advance=1)


def setup_signals(agent: OSINTAgent) -> None:
    """Register signal handlers for graceful shutdown."""

    def handle_signal(*_args: Any) -> None:
        console.print("\n[bold red]Interrupt received! Aborting scans gracefully...[/]")
        # Try common abort methods
        if hasattr(agent, "abort_scan"):
            agent.abort_scan()
        elif hasattr(agent, "orchestrator") and hasattr(agent.orchestrator, "abort"):
            agent.orchestrator.abort()
        else:
            # Last resort: cancel the current task
            asyncio.get_running_loop().stop()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            signal.signal(sig, handle_signal)
