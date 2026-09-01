"""UI widgets for the OSINT Nexus TUI."""

import contextlib
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any, Final

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
from osint_nexus.core.type_defs import JSONDict, JSONListContainer, JSONValue, ensure_type
from osint_nexus.core.ui_models import ActivityLevel, FingerprintData, TelemetryData

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

    def on_scan_update(self, _: ScanUpdate) -> None:
        """Handle scan updates."""
        self.query_one(ProgressBar).advance(1)


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

    def update_data(self, intel: IntelligenceObject) -> None:
        """Updates the dashboard table with new intelligence data."""
        intel_data = self._extract_intel_data(intel)
        self.data.update(intel_data)
        self.table.clear()
        for key, value in intel_data.items():
            self.table.add_row(key, value)
        self.refresh()

    def _extract_intel_data(self, intel: IntelligenceObject) -> dict[str, str]:
        """Extracts and formats relevant information from intelligence."""
        metadata = intel.metadata
        device_results = metadata.get("device_inference", {})

        return {
            "Fingerprint": self._build_fingerprint_summary(device_results),
            "Footprint": str(metadata.get("footprint", "Active")),
            "Canvas": self._get_canvas_status(intel),
            "Useragent": "See Fingerprint",
        }

    def _build_fingerprint_summary(self, device_results: Any) -> str:
        """Builds a summary string from device inference results."""
        if not isinstance(device_results, Mapping):
            return "No Data"

        fingerprint_summary = self._get_all_results(device_results)

        return ", ".join(fingerprint_summary) if fingerprint_summary else "No Data"

    def _get_all_results(self, device_results: Mapping[Any, Any]) -> list[str]:
        """Collects all strategy results."""
        return [
            result
            for strategy in FingerprintStrategy
            if (result := self._get_strategy_result(device_results, strategy)) is not None
        ]

    def _get_strategy_result(
        self, device_results: Mapping[Any, Any], strategy: FingerprintStrategy
    ) -> str | None:
        """Extracts a formatted string for a specific fingerprint strategy."""
        result = device_results.get(strategy.key)
        if isinstance(result, Mapping) and "data" in result:
            val = result["data"].get(strategy.data_key)
            if val:
                return f"{strategy.label}: {val}"
        return None

    def _get_canvas_status(self, intel: IntelligenceObject) -> str:
        """Returns the canvas status based on presence of visuals."""
        if intel.visuals and (intel.visuals.profile_picture or intel.visuals.banner_image):
            return "Visuals Present"
        return "Text/Data Only"

    def update(self, intel: IntelligenceObject) -> None:
        """Update intelligence data."""
        if not intel.found:
            return

        self.data.update(self._extract_intel_data(intel))

        self.table.clear()
        for key, value in self.data.items():
            self.table.add_row(key, value)
        self.refresh()

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        self.update(message.intel)


class TelemetryPanel(Static):
    """Renders Telemetry data (Accessibility: Uses DataTable for screen reader compatibility)."""

    def compose(self) -> ComposeResult:
        table = DataTable()
        table.add_columns("Metric", "Value")
        yield table

    def update(self, intel: IntelligenceObject) -> None:
        """Updates telemetry table by extracting data from IntelligenceObject."""
        metadata = intel.metadata
        telemetry_val = metadata.get("telemetry")
        fingerprint_val = metadata.get("fingerprint_results")

        telemetry_data = self._parse_telemetry(telemetry_val)
        fingerprint = self._parse_fingerprint(fingerprint_val)

        if fingerprint:
            if telemetry_data:
                telemetry_data.fingerprint_results = fingerprint
            else:
                telemetry_data = TelemetryData(
                    dns_leak="N/A",
                    connection_type="N/A",
                    hardware_fingerprint="N/A",
                    fingerprint_results=fingerprint,
                )

        if telemetry_data:
            self._update_table(telemetry_data)

    def _as_dict(self, val: JSONValue) -> dict[str, JSONValue] | None:
        if isinstance(val, JSONDict):
            return val.root
        if isinstance(val, dict):
            return val
        return None

    def _parse_telemetry(self, telemetry_val: JSONValue) -> TelemetryData | None:
        telemetry_raw = self._as_dict(telemetry_val)
        if not telemetry_raw:
            return None
        with contextlib.suppress(ValueError):
            return TelemetryData(
                dns_leak=str(telemetry_raw.get("dns_leak", "N/A")),
                connection_type=str(telemetry_raw.get("connection_type", "N/A")),
                hardware_fingerprint=str(telemetry_raw.get("hardware_fingerprint", "N/A")),
            )
        return None

    def _parse_fingerprint(self, fingerprint_val: JSONValue) -> FingerprintData | None:
        fingerprint_raw = self._as_dict(fingerprint_val)
        if not fingerprint_raw:
            return None
        with contextlib.suppress(ValueError):
            suspicious_val = fingerprint_raw.get("suspicious", False)
            risk_score_val = fingerprint_raw.get("risk_score", 0.0)
            risk_level_val = fingerprint_raw.get("risk_level", "Low")
            action_val = fingerprint_raw.get("recommended_action", "None")
            summary_val = fingerprint_raw.get("summary", "No summary")

            return FingerprintData(
                suspicious=bool(ensure_type(suspicious_val, bool)),
                risk_score=float(ensure_type(risk_score_val, (float, int)) or 0.0),
                risk_level=str(ensure_type(risk_level_val, str) or "Low"),
                recommended_action=str(ensure_type(action_val, str) or "None"),
                summary=str(ensure_type(summary_val, str) or "No summary"),
            )
        return None

    def _update_table(self, telemetry_data: TelemetryData) -> None:
        table = self.query_one(DataTable)
        table.clear()
        table.add_row("DNS Leak", telemetry_data.dns_leak)
        table.add_row("Connection", telemetry_data.connection_type)
        table.add_row("HW Fingerprint", telemetry_data.hardware_fingerprint)

        if telemetry_data.fingerprint_results:
            table.add_row("[bold magenta]--- Fingerprint ---[/]", "")
            table.add_row("Suspicious", str(telemetry_data.fingerprint_results.suspicious))
            table.add_row("Risk Score", f"{telemetry_data.fingerprint_results.risk_score:.2f}")
            table.add_row("Risk Level", telemetry_data.fingerprint_results.risk_level)
            table.add_row("Recommended Action", telemetry_data.fingerprint_results.recommended_action)
            table.add_row("Summary", telemetry_data.fingerprint_results.summary)
        self.refresh()

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        self.update(message.intel)


class RelationshipPanel(Static):
    """Renders Relationships as a Tree (Accessibility: Tree widget is keyboard accessible)."""

    def compose(self) -> ComposeResult:
        yield Tree("Relationships")

    def update(self, intel: IntelligenceObject) -> None:
        """Updates relationship tree by extracting from metadata."""
        relationships_val = intel.metadata.get("relationships")
        relationships: list[str] = []

        if isinstance(relationships_val, list):
            relationships = [str(r) for r in relationships_val]
        elif isinstance(relationships_val, JSONListContainer):
            relationships = [str(r) for r in relationships_val.root]

        tree = self.query_one(Tree)
        tree.root.remove_children()
        for rel in relationships:
            tree.root.add(rel)
        self.refresh()

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        self.update(message.intel)


class HeatmapPanel(Static):
    """Renders Activity Heatmap (Accessibility: Descriptive labels, color independence)."""

    def compose(self) -> ComposeResult:
        yield Static("Activity: [None]", id="heatmap-label")

    def update(self, intel: IntelligenceObject) -> None:
        """Updates heatmap status by extracting activity from metadata."""
        activity_val = intel.metadata.get("activity")

        # Helper to safely extract dictionary
        def as_dict(val: JSONValue) -> dict[str, JSONValue] | None:
            if isinstance(val, JSONDict):
                return val.root
            if isinstance(val, dict):
                return val
            return None

        activity_raw = as_dict(activity_val)
        if activity_raw:
            try:
                level_val = activity_raw.get("level", "Inactive")
                trend_val = activity_raw.get("trend", "Neutral")
                activity = ActivityLevel(
                    level=str(ensure_type(level_val, str) or "Inactive"),
                    trend=str(ensure_type(trend_val, str) or "Neutral"),
                )
                self.query_one("#heatmap-label", Static).update(
                    f"Activity: [bold cyan]{activity.level}[/] (Trend: {activity.trend})"
                )
            except ValueError:
                # Log invalid format, maybe to a global logger
                pass
        self.refresh()

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        self.update(message.intel)


class LogPanel(Static):
    """Renders the scrollable log/error panel."""

    def compose(self) -> ComposeResult:
        yield RichLog(highlight=True, markup=True)

    def update(self, intel: IntelligenceObject) -> None:
        """Log with themed colors."""
        color = COLOR_FOUND if intel.found else COLOR_NOT_FOUND
        status = "Found" if intel.found else "Not Found"
        self.query_one(RichLog).write(f"Analyzed {intel.platform}: [{color}]{status}[/]")

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        self.update(message.intel)


class MetricsGraph(Static):
    """Displays success/failure ratio as a simple bar."""

    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id)
        self.successes: int = 0
        self.failures: int = 0

    def update_metrics(self, successes: int, failures: int) -> None:
        """Update metrics externally."""
        self.successes = successes
        self.failures = failures
        self._refresh_graph()

    def update(self, intel: IntelligenceObject) -> None:
        """Update the metrics display based on the latest intelligence."""
        if "error" in intel.metadata:
            self.failures += 1
        else:
            self.successes += 1
        self._refresh_graph()

    def _refresh_graph(self) -> None:
        """Refresh the graph display."""
        total = self.successes + self.failures
        if total == 0:
            graph = "No data yet."
        else:
            s_bar = "█" * (self.successes * METRICS_BAR_WIDTH // total)
            f_bar = "░" * (self.failures * METRICS_BAR_WIDTH // total)
            graph = f"{s_bar}{f_bar}"
        super().update(f"[cyan]{graph}[/]\n{self.successes} success | {self.failures} failure")

    def on_scan_update(self, message: ScanUpdate) -> None:
        """Handle scan updates."""
        self.update(message.intel)
