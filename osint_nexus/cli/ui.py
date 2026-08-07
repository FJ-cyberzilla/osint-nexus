from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import ProgressBar

from osint_nexus.cli.components.panels import HelpPanel, SettingsPanel
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


class OSINTApp(App[None]):
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
        border: solid grey;
    }
    """

    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, agent: OSINTAgent, username: str, total: int, timeout: float) -> None:
        super().__init__()
        self.agent = agent
        self.username = username
        self.total = total
        self.timeout = timeout
        self._successes = 0
        self._failures = 0
        self._scan_finished = False

    def compose(self) -> ComposeResult:
        yield Container(
            Header(self.username, id="header"),
            ReconProgress(self.total, id="progress"),
            Horizontal(
                IntelligenceDashboard(id="dashboard"),
                MetricsGraph(id="metrics"),
                SettingsPanel(id="settings"),
            ),
            LogPanel(id="logs"),
            HelpPanel(id="help"),
            id="main-container",
        )

    def on_mount(self) -> None:
        """Start the scan worker."""
        self.run_worker(self.scan_worker(), exclusive=True)

    async def scan_worker(self) -> None:
        """Scanner worker."""
        async for intel in self.agent.run_scan(username=self.username, timeout=self.timeout):
            self.post_message(ScanUpdate(intel))
        self._scan_finished = True

    async def action_quit(self) -> None:
        """Restrict quit to after scan."""
        if not self._scan_finished:
            return
        await super().action_quit()

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        intel = message.intel

        # Update dashboard
        self.query_one("#dashboard", IntelligenceDashboard).update_data(intel)

        # Update progress bar
        self.query_one("#progress", ReconProgress).query_one(ProgressBar).advance(1)

        # Update logs
        self.query_one("#logs", LogPanel).write_log(intel.platform, intel.found)

        # Update metrics
        if "error" in intel.metadata:
            self._failures += 1
        else:
            self._successes += 1
        self.query_one("#metrics", MetricsGraph).update_metrics(self._successes, self._failures)
