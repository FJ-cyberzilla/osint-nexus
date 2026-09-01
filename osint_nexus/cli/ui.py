from dataclasses import dataclass
from typing import Self

from beartype import beartype
from rich.console import Console
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import ProgressBar

from osint_nexus.cli.components.panels import HelpPanel, SettingsPanel
from osint_nexus.cli.theme import HEADER_HEIGHT, LOG_PANEL_HEIGHT, METRICS_GRAPH_WIDTH, PROGRESS_BAR_HEIGHT
from osint_nexus.cli.widgets import (
    Banner,
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

console: Console = Console()


@beartype
@dataclass
class ScanConfig:
    """Zero-comma parameter container for OSINTApp initialization."""

    agent: OSINTAgent
    username: str
    total: int
    timeout: float


class OSINTApp(App[None]):
    """Main Textual application for OSINT Nexus."""

    CSS: str = f"""
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

    BINDINGS: list[tuple[str, str, str]] = [("ctrl+q", "quit", "Quit")]

    def __init__(self: Self, config: ScanConfig) -> None:
        super().__init__()
        self.agent: OSINTAgent = config.agent
        self.username: str = config.username
        self.total: int = config.total
        self.timeout: float = config.timeout
        self._scan_finished: bool = False

    def compose(self: Self) -> ComposeResult:
        yield Container(
            Banner(id="banner"),
            Header(id="header"),
            ReconProgress(id="progress"),
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

    def on_mount(self: Self) -> None:
        """Start the scan worker."""
        self.run_worker(self.scan_worker(), exclusive=True)

    async def scan_worker(self: Self) -> None:
        """Scanner worker."""
        async for intel in self.agent.run_scan(username=self.username, timeout=self.timeout):
            self.post_message(ScanUpdate(intel))
        self._scan_finished = True

    async def action_quit(self: Self) -> None:
        """Restrict quit to after scan."""
        if not self._scan_finished:
            return
        await super().action_quit()

    def on_scan_update(self: Self, message: ScanUpdate) -> None:
        """Handle scan updates by delegating to specialized updater methods."""
        intel: IntelligenceObject = message.intel

        self._update_dashboard(intel)
        self._update_progress_bar()
        self._update_logs(intel)
        self._update_metrics(intel)
        self._update_advanced_intel(intel)

    def _update_dashboard(self: Self, intel: IntelligenceObject) -> None:
        """Update the intelligence dashboard."""
        self.query_one("#dashboard", IntelligenceDashboard).update(intel)

    def _update_progress_bar(self: Self) -> None:
        """Advance the progress bar."""
        self.query_one("#progress", ReconProgress).query_one(ProgressBar).advance(1)

    def _update_logs(self: Self, intel: IntelligenceObject) -> None:
        """Write to the log panel."""
        self.query_one("#logs", LogPanel).update(intel)

    def _update_metrics(self: Self, intel: IntelligenceObject) -> None:
        """Update the success/failure metrics graph."""
        self.query_one("#metrics", MetricsGraph).update(intel)

    def _update_advanced_intel(self: Self, intel: IntelligenceObject) -> None:
        """Update telemetry, relationships, and heatmap panels."""
        if not intel.found:
            return

        self.query_one("#telemetry", TelemetryPanel).update(intel)
        self._update_relationship_panel(intel)
        self._update_activity_panel(intel)

    def _update_telemetry_panel(self: Self, intel: IntelligenceObject) -> None:
        """Helper to update telemetry panel."""
        self.query_one("#telemetry", TelemetryPanel).update(intel)

    def _update_relationship_panel(self: Self, intel: IntelligenceObject) -> None:
        """Helper to update relationship panel."""
        self.query_one("#relationships", RelationshipPanel).update(intel)

    def _update_activity_panel(self: Self, intel: IntelligenceObject) -> None:
        """Helper to update activity panel."""
        self.query_one("#heatmap", HeatmapPanel).update(intel)
