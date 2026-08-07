from typing import Any

from PyQt6.QtCore import QUrl
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView

from osint_nexus.core.telemetry.bridge import (
    TelemetryLoggerProtocol,
    WebViewBridge,
)
from osint_nexus.core.telemetry.probes.hardware_telemetry import (
    ADVANCED_TELEMETRY_JS,
)


class PyQtBrowserEngine(QWebEngineView):  # type: ignore
    """Linux / Desktop PyQt6 Native WebEngine Implementation with QWebChannel."""

    def __init__(
        self,
        telemetry_client: TelemetryLoggerProtocol | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        # Step 1: Instantiate the Bridge
        self.bridge = WebViewBridge(telemetry_client=telemetry_client)

        # Step 2: Configure QWebChannel & Register Object
        self.channel = QWebChannel()
        self.channel.registerObject("backendBridge", self.bridge)

        # Step 3: Attach Channel to Page
        page = self.page()
        if page is not None:
            page.setWebChannel(self.channel)

        # Connect load finished signal
        self.loadFinished.connect(self._handle_load_finished)

    def run_navigation(self, url: str) -> None:
        self.setUrl(QUrl(url))

    def _handle_load_finished(self, success: bool) -> None:
        """Executes the telemetry probe and links QWebChannel transport once loaded."""
        if success:
            page = self.page()
            if page is not None:
                # Step 4: Initialize QWebChannel transport on the frontend
                page.runJavaScript(
                    """
                    if (typeof QWebChannel !== 'undefined' && window.qt && window.qt.webChannelTransport) {
                        new QWebChannel(window.qt.webChannelTransport, function(channel) {
                            window.backendBridge = channel.objects.backendBridge;
                        });
                    }
                    """
                )
                # Step 5: Execute advanced telemetry probe script
                page.runJavaScript(ADVANCED_TELEMETRY_JS)
