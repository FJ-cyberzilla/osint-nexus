from textual.app import ComposeResult
from textual.containers import Modal, Vertical
from textual.widgets import Button, Input, Label

from osint_nexus.utils.credentials import CredentialManager


class ApiKeyModal(Modal):
    """Secure modal for entering the Fingerbank API Key."""

    def __init__(self, on_save: callable) -> None:
        super().__init__()
        self.on_save = on_save
        self.cred_manager = CredentialManager()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Enter Fingerbank API Key:"),
            Input(placeholder="API Key", password=True, id="api-key-input"),
            Button("Save", variant="primary", id="save-btn"),
            id="modal-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            api_key = self.query_one("#api-key-input", Input).value
            if api_key:
                self.cred_manager.set_credential("OSINT_FINGERBANK_API_KEY", api_key)
                self.on_save()
                self.dismiss()
