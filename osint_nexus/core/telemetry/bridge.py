import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol

from osint_nexus.core.device_inference import (
    DeviceInferenceEngine,
    DeviceProfile,
)

try:
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    from collections.abc import Callable
    from typing import TypeVar

    _F = TypeVar("_F", bound=Callable[..., Any])

    class QObject:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    def pyqtSignal(*args: Any, **kwargs: Any) -> Any:
        return None

    def pyqtSlot(*args: Any, **kwargs: Any) -> Callable[[_F], _F]:
        def decorator(func: _F) -> _F:
            return func

        return decorator


logger = logging.getLogger("osint_nexus.telemetry.bridge")


class TelemetryLoggerProtocol(Protocol):
    def log(self, data: dict[str, Any]) -> None: ...


class WebViewAction(ABC):
    @abstractmethod
    def execute(self, telemetry_registry: Any, data: dict[str, Any]) -> Any:
        pass


class TelemetryAction(WebViewAction):
    def execute(self, telemetry_registry: Any, data: dict[str, Any]) -> Any:
        return telemetry_registry.run_all()


class WebViewBridge(QObject):  # type: ignore[misc]
    # Define signal if PyQt is available
    telemetry_received = pyqtSignal(dict) if PYQT_AVAILABLE else None

    def __init__(
        self,
        telemetry_registry: Any | None = None,
        telemetry_client: TelemetryLoggerProtocol | None = None,
    ) -> None:
        super().__init__()
        self.telemetry_registry = telemetry_registry
        self.telemetry_client = telemetry_client
        self.inference_engine = DeviceInferenceEngine()
        self._actions: dict[str, WebViewAction] = {"run_telemetry": TelemetryAction()}

    @pyqtSlot(str)  # type: ignore[untyped-decorator]
    def submit_telemetry(self, raw_json_data: str) -> None:
        """Slot called directly from JavaScript when telemetry is pushed."""
        try:
            data: dict[str, Any] = json.loads(raw_json_data)

            if self.telemetry_client is not None:
                self.telemetry_client.log(data)

            inferred_profile: DeviceProfile = self.inference_engine.analyze(data)

            if PYQT_AVAILABLE and self.telemetry_received:
                self.telemetry_received.emit(inferred_profile)
            else:
                logger.info(f"Telemetry inferred: {inferred_profile}")

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"Failed to parse incoming telemetry: {e}")

    async def handle_message(self, message: str) -> str:
        """Handle messages coming from the WebView (Async/Playwright style)."""
        logger.debug(f"Received message: {message}")
        try:
            data = json.loads(message)
            action_name = data.get("action")

            if action_name not in self._actions:
                return json.dumps({"status": "error", "message": f"Unknown action: {action_name}"})

            action = self._actions[action_name]

            if self.telemetry_registry is None:
                return json.dumps({"status": "error", "message": "Telemetry registry not initialized"})

            results = action.execute(self.telemetry_registry, data)

            return json.dumps({"status": "success", "results": results})
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message", exc_info=True)
            return json.dumps({"status": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.exception("Error handling bridge message")
            return json.dumps({"status": "error", "message": str(e)})
