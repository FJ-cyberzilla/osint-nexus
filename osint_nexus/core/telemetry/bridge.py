import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Protocol, cast

from osint_nexus.core.device_inference import (
    DeviceInferenceEngine,
    DeviceProfile,
)
from osint_nexus.core.telemetry.registry import TelemetryRegistry


# Define a protocol for QObject-like behavior to avoid 'Any' in type hints
class QObjectProtocol(Protocol):
    def connect(self, slot: Callable[..., Any]) -> None: ...
    def disconnect(self, slot: Callable[..., Any]) -> None: ...


try:
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    # Define mocks that are more type-compliant
    class QObject:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    def pyqtSignal(*args: Any, **kwargs: Any) -> Any:
        return None

    def pyqtSlot(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


logger = logging.getLogger("osint_nexus.telemetry.bridge")
...


class TelemetryLoggerProtocol(Protocol):
    def log(self, data: dict[str, Any]) -> None: ...


class WebViewAction(ABC):
    @abstractmethod
    async def execute(self, telemetry_registry: TelemetryRegistry, data: dict[str, Any]) -> Any:
        pass


class TelemetryAction(WebViewAction):
    async def execute(self, telemetry_registry: TelemetryRegistry, data: dict[str, Any]) -> Any:
        return await telemetry_registry.run_all()


class WebViewBridge(QObject):
    # Define signal if PyQt is available
    telemetry_received: Any = pyqtSignal(dict) if PYQT_AVAILABLE else None

    def __init__(
        self,
        telemetry_registry: TelemetryRegistry | None = None,
        telemetry_client: TelemetryLoggerProtocol | None = None,
    ) -> None:
        super().__init__()
        self.telemetry_registry = telemetry_registry
        self.telemetry_client = telemetry_client
        self.inference_engine = DeviceInferenceEngine()
        self._actions: dict[str, WebViewAction] = {"run_telemetry": TelemetryAction()}

    @pyqtSlot(str)
    def submit_telemetry(self, raw_json_data: str) -> None:
        """Slot called directly from JavaScript when telemetry is pushed."""
        try:
            data: dict[str, Any] = cast(dict[str, Any], json.loads(raw_json_data))

            if self.telemetry_client is not None:
                self.telemetry_client.log(data)

            inferred_profile: DeviceProfile = self.inference_engine.analyze(data)

            if PYQT_AVAILABLE and self.telemetry_received is not None:
                self.telemetry_received.emit(inferred_profile)
            else:
                logger.info("Telemetry inferred: %s", inferred_profile)

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error("Failed to parse incoming telemetry: %s", e)

    async def handle_message(self, message: str) -> str:
        """Handle messages coming from the WebView (Async/Playwright style)."""
        logger.debug("Received message: %s", message)
        try:
            data = cast(dict[str, Any], json.loads(message))
            action_name = cast(str, data.get("action", ""))

            if action_name not in self._actions:
                return json.dumps({"status": "error", "message": f"Unknown action: {action_name}"})

            action = self._actions[action_name]

            if self.telemetry_registry is None:
                return json.dumps({"status": "error", "message": "Telemetry registry not initialized"})

            results = await action.execute(self.telemetry_registry, data)

            return json.dumps({"status": "success", "results": results})
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message", exc_info=True)
            return json.dumps({"status": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.exception("Error handling bridge message")
            return json.dumps({"status": "error", "message": str(e)})
