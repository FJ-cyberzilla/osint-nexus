from collections.abc import Mapping
from typing import cast

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, ProgressBar, RichLog, Static

from osint_nexus.cli.theme import (
    COLOR_FOUND,
    COLOR_NOT_FOUND,
    COLOR_PROGRESS_FAILURE,
    COLOR_PROGRESS_SUCCESS,
    METRICS_BAR_WIDTH,
)
from osint_nexus.core.intelligence import IntelligenceObject


class ScanUpdate(Message):
    """Message sent when new intelligence is found."""

    def __init__(self, intel: IntelligenceObject) -> None:
        super().__init__()
        self.intel = intel


class Header(Static):
    """Renders the top branding and target info panel."""

    def __init__(self, username: str, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.username = username

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold cyan]OSINT Nexus[/] | [dim]Target:[/] [bold white]{self.username}[/]",
        )


class ReconProgress(Static):
    """Renders the real-time progress bar."""

    def __init__(self, total: int, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.total = total

    def compose(self) -> ComposeResult:
        # Multi-colored progress bar
        bar = ProgressBar(total=self.total, id="progress-bar")
        bar.styles.bar_color = COLOR_PROGRESS_SUCCESS
        bar.styles.bar_background = COLOR_PROGRESS_FAILURE
        yield bar


class IntelligenceDashboard(Static):
    """Renders the Intelligence Dashboard (Fingerprint, Footprint, etc.)."""

    table: DataTable[str]

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.data: dict[str, str] = {
            "Fingerprint": "Pending",
            "Footprint": "Pending",
            "Canvas": "Pending",
            "Useragent": "Pending",
        }

    def compose(self) -> ComposeResult:
        self.table = DataTable()
        self.table.add_columns("Category", "Details")
        for key, value in self.data.items():
            self.table.add_row(key, value)
        yield self.table

    def _extract_intel_data(self, intel: IntelligenceObject) -> dict[str, str]:
        """Extracts and formats relevant information from intelligence."""
        # Ensure metadata is treated as a mapping for .get()
        metadata = cast(Mapping[str, object], intel.metadata)

        return {
            "Fingerprint": str(metadata.get("fingerprint", "Detected")),
            "Footprint": str(metadata.get("footprint", "Active")),
            "Canvas": (
                "Visuals Present"
                if (intel.visuals and (intel.visuals.profile_picture or intel.visuals.banner_image))
                else "Text/Data Only"
            ),
            "Useragent": str(metadata.get("device_inference", {}).get("os_guess", "Generic")),
        }

    def update_data(self, intel: IntelligenceObject) -> None:
        """Update intelligence data."""
        if not intel.found:
            return

        self.data.update(self._extract_intel_data(intel))

        self.table.clear()
        for key, value in self.data.items():
            self.table.add_row(key, value)


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

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
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
