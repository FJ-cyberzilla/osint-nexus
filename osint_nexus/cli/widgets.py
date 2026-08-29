"""UI widgets for the OSINT Nexus TUI."""

from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Final

from rich.panel import Panel
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, ProgressBar, RichLog, Static, Tree

from osint_nexus.cli.theme import (
    COLOR_FOUND,
    COLOR_NOT_FOUND,
    COLOR_PROGRESS_FAILURE,
    COLOR_PROGRESS_SUCCESS,
    METRICS_BAR_WIDTH,
)
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.ui_models import ActivityLevel, TelemetryData

# Widget Constants
DEFAULT_PROGRESS_TOTAL: Final[int] = 0


class Banner(Static):
    """Renders the banner from 1.txt in a green box."""

    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id)
        # Load the banner from the root directory
        try:
            with open(Path(__file__).parent / "../../1.txt") as f:
                self.banner = f.read()
        except FileNotFoundError:
            self.banner = "OSINT Nexus"

    def compose(self) -> ComposeResult:
        # Wrap the banner in a green box
        yield Static(
            Panel(
                f"[green]{self.banner}[/]",
                border_style="green",
                title="OSINT Nexus",
            )
        )


class FingerprintStrategy(Enum):
    TCP = ("tcp_stack", "inferred_os", "TCP")
    TLS = ("tls_ja3", "inferred_device", "TLS")
    HTTP = ("http_headers", "platform", "HTTP")

    def __init__(self, key: str, data_key: str, label: str) -> None:
        self.key = key
        self.data_key = data_key
        self.label = label


class ScanUpdate(Message):
    """Message sent when new intelligence is found."""

    def __init__(self, intel: IntelligenceObject) -> None:
        super().__init__()
        self.intel = intel


class Header(Static):
    """Renders the top branding and target info panel."""

    def __init__(self, username: str, id: str | None = None) -> None:
        super().__init__(id=id)
        self.username = username

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold cyan]OSINT Nexus[/] | [dim]Target:[/] [bold white]{self.username}[/]",
        )


class ReconProgress(Static):
    """Renders the real-time progress bar."""

    def __init__(self, total: int, id: str | None = None) -> None:
        super().__init__(id=id)
        self.total = total

    def compose(self) -> ComposeResult:
        # Multi-colored progress bar
        progress_bar = ProgressBar(total=self.total, id="progress-bar", show_eta=False, show_percentage=True)
        # Textual style modification: set style properties explicitly
        progress_bar.styles.background = COLOR_PROGRESS_FAILURE
        progress_bar.styles.color = COLOR_PROGRESS_SUCCESS
        yield progress_bar


class IntelligenceDashboard(Static):
    """Renders the Intelligence Dashboard (Fingerprint, Footprint, etc.)."""

    table: DataTable[str] = DataTable()

    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id)
        self.data: dict[str, str] = {
            "Fingerprint": "Pending",
            "Footprint": "Pending",
            "Canvas": "Pending",
            "Useragent": "Pending",
        }

    def compose(self) -> ComposeResult:
        self.table.add_columns("Category", "Details")
        for key, value in self.data.items():
            self.table.add_row(key, value)
        yield self.table

    def _extract_intel_data(self, intel: IntelligenceObject) -> dict[str, str]:
        """Extracts and formats relevant information from intelligence."""
        metadata = intel.metadata

        # New: Aggregate device fingerprint results using Enum registry
        device_results = metadata.get("device_inference", {})

        fingerprint_summary = []
        if isinstance(device_results, Mapping):
            for strategy in FingerprintStrategy:
                result = device_results.get(strategy.key)
                if isinstance(result, Mapping) and "data" in result:
                    # Ensure we have data before displaying
                    val = result["data"].get(strategy.data_key)
                    if val:
                        fingerprint_summary.append(f"{strategy.label}: {val}")

        return {
            "Fingerprint": ", ".join(fingerprint_summary) if fingerprint_summary else "No Data",
            "Footprint": str(metadata.get("footprint", "Active")),
            "Canvas": (
                "Visuals Present"
                if (intel.visuals and (intel.visuals.profile_picture or intel.visuals.banner_image))
                else "Text/Data Only"
            ),
            "Useragent": "See Fingerprint",
        }

    def update_data(self, intel: IntelligenceObject) -> None:
        """Update intelligence data."""
        if not intel.found:
            return

        self.data.update(self._extract_intel_data(intel))

        self.table.clear()
        for key, value in self.data.items():
            self.table.add_row(key, value)


class TelemetryPanel(Static):
    """Renders Telemetry data (Accessibility: Uses DataTable for screen reader compatibility)."""

    def compose(self) -> ComposeResult:
        table = DataTable()
        table.add_columns("Metric", "Value")
        yield table

    def update_telemetry(self, telemetry: TelemetryData) -> None:
        """Updates telemetry table with structured data."""
        table = self.query_one(DataTable)
        table.clear()
        table.add_row("DNS Leak", telemetry.dns_leak)
        table.add_row("Connection", telemetry.connection_type)
        table.add_row("HW Fingerprint", telemetry.hardware_fingerprint)

        if telemetry.fingerprint_results:
            table.add_row("[bold magenta]--- Fingerprint ---[/]", "")
            table.add_row("Suspicious", str(telemetry.fingerprint_results.suspicious))
            table.add_row("Risk Score", f"{telemetry.fingerprint_results.risk_score:.2f}")
            table.add_row("Risk Level", telemetry.fingerprint_results.risk_level)
            table.add_row("Recommended Action", telemetry.fingerprint_results.recommended_action)
            table.add_row("Summary", telemetry.fingerprint_results.summary)


class RelationshipPanel(Static):
    """Renders Relationships as a Tree (Accessibility: Tree widget is keyboard accessible)."""

    def compose(self) -> ComposeResult:
        yield Tree("Relationships")

    def update_relationships(self, relationships: list[str]) -> None:
        """Updates relationship tree."""
        tree = self.query_one(Tree)
        tree.root.remove_children()
        for rel in relationships:
            tree.root.add(rel)


class HeatmapPanel(Static):
    """Renders Activity Heatmap (Accessibility: Descriptive labels, color independence)."""

    def compose(self) -> ComposeResult:
        yield Static("Activity: [None]", id="heatmap-label")

    def update_heatmap(self, activity: ActivityLevel) -> None:
        """Updates heatmap status using structured model."""
        self.query_one("#heatmap-label", Static).update(
            f"Activity: [bold cyan]{activity.level}[/] (Trend: {activity.trend})"
        )


class LogPanel(Static):
    """Renders the scrollable log/error panel."""

    def compose(self) -> ComposeResult:
        yield RichLog(highlight=True, markup=True)

    def write_log(self, platform: str, found: bool) -> None:
        """Log with themed colors."""
        color = COLOR_FOUND if found else COLOR_NOT_FOUND
        status = "Found" if found else "Not Found"
        self.query_one(RichLog).write(f"Analyzed {platform}: [{color}]{status}[/]")


class MetricsGraph(Static):
    """Displays success/failure ratio as a simple bar."""

    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id)
        self.successes: int = 0
        self.failures: int = 0

    def update_metrics(self, successes: int, failures: int) -> None:
        """Update the metrics display."""
        self.successes = successes
        self.failures = failures
        total = successes + failures
        if total == 0:
            graph = "No data yet."
        else:
            s_bar = "█" * (self.successes * METRICS_BAR_WIDTH // total)
            f_bar = "░" * (self.failures * METRICS_BAR_WIDTH // total)
            graph = f"{s_bar}{f_bar}"
        self.update(f"[cyan]{graph}[/]\n{self.successes} success | {self.failures} failure")
