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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.fingerprint = "Pending"
        self.footprint = "Pending"
        self.canvas = "Pending"
        self.useragent = "Pending"

    def compose(self) -> ComposeResult:
        table = DataTable()
        table.add_columns("Category", "Details")
        table.add_rows(
            [
                ("Fingerprint", self.fingerprint),
                ("Footprint", self.footprint),
                ("Canvas", self.canvas),
                ("Useragent", self.useragent),
            ]
        )
        yield table

    def update_data(self, intel: Any) -> None:
        """Update intelligence data."""
        if not intel.found:
            return
        # ... logic to update table ...
        # Textual DataTable updates will happen here


class LogPanel(Static):
    """Renders the scrollable log/error panel."""

    def compose(self) -> ComposeResult:
        yield RichLog(highlight=True, markup=True)


class MetricsGraph(Static):
    """Renders a simple ASCII success/failure metric graph."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.successes = 0
        self.failures = 0

    def compose(self) -> ComposeResult:
        yield Static("No data yet.", id="metrics-graph")
