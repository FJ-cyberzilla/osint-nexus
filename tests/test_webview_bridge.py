import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from osint_nexus.core.telemetry.bridge import PYQT_AVAILABLE, WebViewBridge


class MockTelemetryRegistry:
    def __init__(self) -> None:
        self.run_all = MagicMock(return_value={"dns": {"leaked": False}})


class MockTelemetryClient:
    def __init__(self) -> None:
        self.logs: list[dict[str, Any]] = []

    def log(self, data: dict[str, Any]) -> None:
        self.logs.append(data)


@pytest.mark.asyncio
async def test_webview_bridge_async() -> None:
    """Tests the async handle_message (Playwright style) bridge."""
    mock_registry = MockTelemetryRegistry()
    bridge = WebViewBridge(telemetry_registry=mock_registry)

    # Test run_telemetry action
    message = json.dumps({"action": "run_telemetry"})
    response = await bridge.handle_message(message)

    response_data = json.loads(response)
    assert response_data["status"] == "success"
    assert response_data["results"] == {"dns": {"leaked": False}}
    mock_registry.run_all.assert_called_once()

    # Test unknown action
    message = json.dumps({"action": "unknown"})
    response = await bridge.handle_message(message)
    response_data = json.loads(response)
    assert response_data["status"] == "error"
    assert "Unknown action" in response_data["message"]


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
def test_bridge_telemetry_processing() -> None:
    """Tests the PyQt6 slot-based telemetry processing."""
    client = MockTelemetryClient()
    bridge = WebViewBridge(telemetry_client=client)

    emitted_signals: list[dict[str, Any]] = []
    # In my hybrid implementation, telemetry_received is None if not PYQT_AVAILABLE
    if bridge.telemetry_received:
        bridge.telemetry_received.connect(lambda profile: emitted_signals.append(profile))

    payload = json.dumps({"webgl_renderer": "Adreno (TM) 740", "cpu_benchmark_ms": 12.4})

    bridge.submit_telemetry(payload)

    assert len(client.logs) == 1
    assert client.logs[0]["webgl_renderer"] == "Adreno (TM) 740"

    assert len(emitted_signals) == 1
    assert emitted_signals[0]["hardware_tier"] == "High-End"
    assert emitted_signals[0]["anomaly_detected"] is False


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
def test_bridge_telemetry_anomaly_detection() -> None:
    """Tests anomaly detection in the telemetry bridge."""
    bridge = WebViewBridge()

    emitted_signals: list[dict[str, Any]] = []
    if bridge.telemetry_received:
        bridge.telemetry_received.connect(lambda profile: emitted_signals.append(profile))

    # Simulating high CPU benchmark loop indicating throttling
    payload = json.dumps({"webgl_renderer": "Unknown GPU", "cpu_benchmark_ms": 75.2})

    bridge.submit_telemetry(payload)

    assert len(emitted_signals) == 1
    assert emitted_signals[0]["anomaly_detected"] is True
    assert emitted_signals[0]["throttle_status"] is not None
