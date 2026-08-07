import json
import logging
from collections.abc import Callable

from osint_nexus.core.device_inference import (
    DeviceInferenceEngine,
    DeviceProfile,
)
from osint_nexus.core.telemetry.bridge import TelemetryDict, TelemetryLoggerProtocol
from osint_nexus.core.telemetry.probes.hardware_telemetry import (
    ADVANCED_TELEMETRY_JS,
)

logger = logging.getLogger(__name__)


class PlaywrightBrowserEngine:
    """Termux / Android / Headless Playwright Telemetry Engine Fallback."""

    def __init__(
        self,
        telemetry_client: TelemetryLoggerProtocol | None = None,
        callback: Callable[[DeviceProfile], None] | None = None,
    ) -> None:
        self.telemetry_client = telemetry_client
        self.callback = callback
        self.inference_engine = DeviceInferenceEngine()

    def _parse_telemetry(self, raw_json_data: str) -> TelemetryDict:
        """Parses and validates telemetry data."""
        data_obj: object = json.loads(raw_json_data)
        if not isinstance(data_obj, dict):
            raise TypeError("Expected dictionary")

        return {
            k: v for k, v in data_obj.items() if isinstance(k, str) and isinstance(v, (str, float, int, bool))
        }

    def _process_telemetry(self, data: TelemetryDict) -> None:
        """Processes and logs telemetry data."""
        if self.telemetry_client is not None:
            self.telemetry_client.log(data)

        inferred_profile: DeviceProfile = self.inference_engine.analyze(data)
        if self.callback is not None:
            self.callback(inferred_profile)
        logger.info("Successfully processed Playwright telemetry.")

    def handle_submit_telemetry(self, _source: object, raw_json_data: str) -> None:
        """Handles telemetry payload injected from Playwright context."""
        try:
            data = self._parse_telemetry(raw_json_data)
            self._process_telemetry(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse Playwright telemetry payload: {e}")

    def run_navigation(self, url: str) -> None:
        """Navigates a target URL and injects the telemetry execution script."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # Expose backend binding mimicking PyQt window.backendBridge
                page.expose_binding(
                    "__playwright_submit_telemetry",
                    self.handle_submit_telemetry,
                )

                page.add_init_script(
                    """
                    window.backendBridge = {
                        submit_telemetry: function(jsonStr) {
                            window.__playwright_submit_telemetry(jsonStr);
                        }
                    };
                    """
                )

                page.goto(url)
                page.evaluate(ADVANCED_TELEMETRY_JS)
                browser.close()
        except ImportError:
            logger.error("Playwright is not installed. Execute `pip install playwright`.")
