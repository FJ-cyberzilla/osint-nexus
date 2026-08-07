"""Modular UI components."""

from textual.app import ComposeResult
from textual.widgets import Static

from osint_nexus.cli.theme import COLOR_HELP


class HelpPanel(Static):
    """Displays a helpful tip."""

    def compose(self) -> ComposeResult:
        yield Static(f"[{COLOR_HELP}]Tip: Use Ctrl+Q to exit after scan completes.[/]", id="help-tip")


class SettingsPanel(Static):
    """Settings interface."""

    def compose(self) -> ComposeResult:
        yield Static("Settings\n--------\nMode: Full\nTimeout: 30s")
