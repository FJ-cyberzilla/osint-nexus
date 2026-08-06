import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Protocol, cast

from osint_nexus.core.device_inference import (
    DeviceInferenceEngine,
    DeviceProfile,
)
from osint_nexus.core.telemetry.registry import TelemetryRegistry

# Define type alias for telemetry data values
type TelemetryValue = str | float | int | bool
type TelemetryDict = dict[str, TelemetryValue]


# Define a protocol for QObject-like behavior to avoid 'Any' in type hints
class QObjectProtocol(Protocol):
    def connect(self, slot: Callable[..., object]) -> None: ...
    def disconnect(self, slot: Callable[..., object]) -> None: ...


try:
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

    # Define mocks that are more type-compliant
    class QObject:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    def pyqtSignal(*args: type, **kwargs: type) -> object:
        return None

    def pyqtSlot(*args: str, **kwargs: str) -> Callable[[Callable[..., None]], Callable[..., None]]:
        def decorator(func: Callable[..., None]) -> Callable[..., None]:
            return func

        return decorator


logger = logging.getLogger("osint_nexus.telemetry.bridge")
...


class TelemetryLoggerProtocol(Protocol):
    def log(self, data: TelemetryDict) -> None: ...


class WebViewAction(ABC):
    @abstractmethod
    async def execute(self, telemetry_registry: TelemetryRegistry, data: TelemetryDict) -> object:
        pass


class TelemetryAction(WebViewAction):
    async def execute(self, telemetry_registry: TelemetryRegistry, data: TelemetryDict) -> object:
        return await telemetry_registry.run_all()


class WebViewBridge(QObject):
    # Define signal if PyQt is available
    telemetry_received: object | None = pyqtSignal(dict) if PYQT_AVAILABLE else None

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
            data_obj: object = json.loads(raw_json_data)
            if not isinstance(data_obj, dict) or not all(isinstance(k, str) for k in data_obj):
                raise TypeError("Expected dictionary with string keys")

            # Simple validation for the values
            if not all(isinstance(v, (str, float, int, bool)) for v in data_obj.values()):
                # Filter invalid values
                data: TelemetryDict = {
                    k: v for k, v in data_obj.items() if isinstance(v, (str, float, int, bool))
                }
            else:
                data = cast(TelemetryDict, data_obj)

            if self.telemetry_client is not None:
                self.telemetry_client.log(data)

            inferred_profile: DeviceProfile = self.inference_engine.analyze(data)

            if (
                PYQT_AVAILABLE
                and self.telemetry_received is not None
                and hasattr(self.telemetry_received, "emit")
            ):
                # We know emit exists if PYQT_AVAILABLE is true for a signal
                self.telemetry_received.emit(inferred_profile)
            else:
                logger.info("Telemetry inferred: %s", inferred_profile)

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error("Failed to parse incoming telemetry: %s", e)

    async def handle_message(self, message: str) -> str:
        """Handle messages coming from the WebView (Async/Playwright style)."""
        logger.debug("Received message: %s", message)
        try:
            data_obj: object = json.loads(message)
            if not isinstance(data_obj, dict) or not all(isinstance(k, str) for k in data_obj):
                raise TypeError("Expected dictionary with string keys")

            # Simple validation for the values
            if not all(isinstance(v, (str, float, int, bool)) for v in data_obj.values()):
                # Filter invalid values
                data: TelemetryDict = {
                    k: v for k, v in data_obj.items() if isinstance(v, (str, float, int, bool))
                }
            else:
                data = cast(TelemetryDict, data_obj)

            action_name = str(data.get("action", ""))

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
