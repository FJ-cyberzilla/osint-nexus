"""TUI Application entry point for OSINT Nexus."""

from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import ProgressBar

from osint_nexus.cli.components.panels import HelpPanel, SettingsPanel
from osint_nexus.cli.theme import (
    HEADER_HEIGHT,
    LOG_PANEL_HEIGHT,
    METRICS_GRAPH_WIDTH,
    PROGRESS_BAR_HEIGHT,
)
from osint_nexus.cli.widgets import (
    Header,
    HeatmapPanel,
    IntelligenceDashboard,
    LogPanel,
    MetricsGraph,
    ReconProgress,
    RelationshipPanel,
    ScanUpdate,
    TelemetryPanel,
)
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.ui_models import ActivityLevel, TelemetryData

console = Console()


class OSINTApp(App[None]):
    """Main Textual application for OSINT Nexus."""

    CSS = f"""
    #main-container {{
        layout: vertical;
        padding: 1;
    }}
    Header {{
        height: {HEADER_HEIGHT};
        border: round cyan;
        padding: 0 1;
    }}
    ReconProgress {{
        height: {PROGRESS_BAR_HEIGHT};
        border: round white;
        margin: 1 0;
        padding: 0 1;
    }}
    IntelligenceDashboard {{
        height: 100%;
        width: 100%;
        border: round blue;
    }}
    MetricsGraph {{
        width: {METRICS_GRAPH_WIDTH};
        border: round magenta;
        padding: 1;
    }}
    TelemetryPanel, RelationshipPanel, HeatmapPanel {{
        border: round green;
        margin: 1;
        padding: 1;
    }}
    LogPanel {{
        height: {LOG_PANEL_HEIGHT};
        border: round grey;
        margin-top: 1;
    }}
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
                Vertical(
                    TelemetryPanel(id="telemetry"),
                    RelationshipPanel(id="relationships"),
                    HeatmapPanel(id="heatmap"),
                ),
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
        """Handle scan updates by delegating to specialized updater methods."""
        intel = message.intel

        self._update_dashboard(intel)
        self._update_progress_bar()
        self._update_logs(intel)
        self._update_metrics(intel)
        self._update_advanced_intel(intel)

    def _update_dashboard(self, intel: IntelligenceObject) -> None:
        """Update the intelligence dashboard."""
        self.query_one("#dashboard", IntelligenceDashboard).update_data(intel)

    def _update_progress_bar(self) -> None:
        """Advance the progress bar."""
        self.query_one("#progress", ReconProgress).query_one(ProgressBar).advance(1)

    def _update_logs(self, intel: IntelligenceObject) -> None:
        """Write to the log panel."""
        self.query_one("#logs", LogPanel).write_log(intel.platform, intel.found)

    def _update_metrics(self, intel: IntelligenceObject) -> None:
        """Update the success/failure metrics graph."""
        if "error" in intel.metadata:
            self._failures += 1
        else:
            self._successes += 1
        self.query_one("#metrics", MetricsGraph).update_metrics(self._successes, self._failures)

    def _update_advanced_intel(self, intel: IntelligenceObject) -> None:
        """Update telemetry, relationships, and heatmap panels."""
        if not intel.found:
            return

        metadata = intel.metadata

        # Map Telemetry
        telemetry_raw = metadata.get("telemetry")
        if isinstance(telemetry_raw, dict):
            try:
                telemetry = TelemetryData(**telemetry_raw)
                self.query_one("#telemetry", TelemetryPanel).update_telemetry(telemetry)
            except ValueError:
                console.log("Invalid telemetry data format.")

        # Map Relationships
        relationships = metadata.get("relationships", [])
        if isinstance(relationships, list):
            self.query_one("#relationships", RelationshipPanel).update_relationships(relationships)

        # Map Activity
        activity_raw = metadata.get("activity")
        if isinstance(activity_raw, dict):
            try:
                activity = ActivityLevel(**activity_raw)
                self.query_one("#heatmap", HeatmapPanel).update_heatmap(activity)
            except ValueError:
                console.log("Invalid activity level data format.")
