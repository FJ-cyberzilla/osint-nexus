from typing import Any

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, ProgressBar, RichLog, Static


class ScanUpdate(Message):
    """Message sent when new intelligence is found."""

    def __init__(self, intel: Any) -> None:
        super().__init__()
        self.intel = intel


class Header(Static):
    """Renders the top branding and target info panel."""

    def __init__(self, username: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.username = username

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold cyan]OSINT Nexus[/] | [dim]Target:[/] [bold white]{self.username}[/]",
        )


class ReconProgress(Static):
    """Renders the real-time progress bar."""

    def __init__(self, total: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.total = total

    def compose(self) -> ComposeResult:
        yield ProgressBar(total=self.total, id="progress-bar")


class IntelligenceDashboard(Static):
    """Renders the Intelligence Dashboard (Fingerprint, Footprint, etc.)."""

    table: DataTable[str]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.data = {
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

    def _extract_intel_data(self, intel: Any) -> dict[str, str]:
        """Extracts and formats relevant information from intelligence."""
        return {
            "Fingerprint": intel.metadata.get("fingerprint", "Detected"),
            "Footprint": intel.metadata.get("footprint", "Active"),
            "Canvas": (
                "Visuals Present"
                if (intel.visuals and (intel.visuals.profile_picture or intel.visuals.banner_image))
                else "Text/Data Only"
            ),
            "Useragent": intel.metadata.get("device_inference", {}).get("os_guess", "Generic"),
        }

    def update_data(self, intel: Any) -> None:
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


class MetricsGraph(Static):
    """Displays success/failure ratio as a simple bar."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.successes = 0
        self.failures = 0

    def update_metrics(self, successes: int, failures: int) -> None:
        """Update the metrics display."""
        self.successes = successes
        self.failures = failures
        total = successes + failures
        if total == 0:
            graph = "No data yet."
        else:
            s_bar = "█" * (successes * 20 // total)
            f_bar = "░" * (failures * 20 // total)
            graph = f"{s_bar}{f_bar}"
        self.update(f"[cyan]{graph}[/]\n{successes} success | {failures} failure")
