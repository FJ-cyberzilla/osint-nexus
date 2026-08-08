"""Modular UI components."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static

from osint_nexus.cli.theme import COLOR_HELP
from osint_nexus.core.ui_models import DeviceProfile


class HelpPanel(Static):
    """Displays a helpful tip."""

    def compose(self) -> ComposeResult:
        yield Static(f"[{COLOR_HELP}]Tip: Use Ctrl+Q to exit after scan completes.[/]", id="help-tip")


class SettingsPanel(Static):
    """Settings interface."""

    def compose(self) -> ComposeResult:
        yield Static("Settings\n--------\nMode: Full\nTimeout: 30s")


class DeviceProfilePanel(Static):
    """Accessibility: Displays device profiling results."""

    def __init__(self, profile: DeviceProfile) -> None:
        super().__init__()
        self.profile = profile

    def compose(self) -> ComposeResult:
        # Accessibility Strategy:
        # - Use Vertical container for logical structure.
        # - Use clear labels for accessibility.
        # - Ensure high contrast (implicit in theme).
        yield Vertical(
            Label(f"Device: {self.profile.device_name}", classes="profile-item"),
            Label(f"Manufacturer: {self.profile.manufacturer}", classes="profile-item"),
            Label(f"OS: {self.profile.os_name}", classes="profile-item"),
            Label(f"Version: {self.profile.version}", classes="profile-item"),
            Label(f"Confidence: {self.profile.confidence_score}%", classes="profile-item"),
            Label(f"Vulnerabilities: {self.profile.vulnerability_message}", classes="profile-item"),
            id="profile-container",
        )
