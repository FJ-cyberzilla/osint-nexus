import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

from osint_nexus.core.device_inference import (
    DeviceInferenceEngine,
    DeviceProfile,
)
from osint_nexus.core.telemetry.registry import TelemetryRegistry
from osint_nexus.core.type_defs import TelemetryDict, TelemetryValue

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

    PYQT_AVAILABLE = True
else:
    # Minimal stub to allow inheritance
    class QObject:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def emit(self, *args: object, **kwargs: object) -> None:
            pass

    # Stub functions for type hinting when PyQt is unavailable
    def pyqtSignal(*args: object, **kwargs: object) -> object:
        return None

    def pyqtSlot(*args: object, **kwargs: object) -> Callable[[Callable[..., object]], Callable[..., object]]:
        def decorator(func: Callable[..., object]) -> Callable[..., object]:
            return func

        return decorator

    PYQT_AVAILABLE = False


logger = logging.getLogger("osint_nexus.telemetry.bridge")


@runtime_checkable
class SignalProtocol(Protocol):
    def emit(self, data: DeviceProfile) -> None: ...


@runtime_checkable
class TelemetryLoggerProtocol(Protocol):
    def log(self, data: TelemetryDict) -> None: ...


class WebViewAction(ABC):
    @abstractmethod
    async def execute(
        self, telemetry_registry: TelemetryRegistry, data: TelemetryDict
    ) -> dict[str, dict[str, object]]:
        pass


class TelemetryAction(WebViewAction):
    async def execute(
        self, telemetry_registry: TelemetryRegistry, data: TelemetryDict
    ) -> dict[str, dict[str, object]]:
        return await telemetry_registry.run_all()


class WebViewBridge(QObject):
    telemetry_received: SignalProtocol | None = pyqtSignal(dict) if PYQT_AVAILABLE else None  # type: ignore[assignment]

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

    def _validate_dict(self, data_obj: object) -> None:
        if not isinstance(data_obj, dict) or not all(isinstance(k, str) for k in data_obj):
            raise TypeError("Expected dictionary with string keys")

    def _clean_data(self, data_obj: dict[str, TelemetryValue]) -> TelemetryDict:
        cleaned: TelemetryDict = {}
        for k, v in data_obj.items():
            if isinstance(v, (str, float, int, bool)):
                cleaned[k] = v
        return cleaned

    def _parse_telemetry(self, raw_json_data: str) -> TelemetryDict:
        data_obj: object = json.loads(raw_json_data)
        self._validate_dict(data_obj)
        if isinstance(data_obj, dict):
            return self._clean_data(cast(dict[str, TelemetryValue], data_obj))
        raise TypeError("Invalid data format")

    def _emit_or_log_profile(self, profile: DeviceProfile) -> None:
        if PYQT_AVAILABLE and isinstance(self.telemetry_received, SignalProtocol):
            self.telemetry_received.emit(profile)
        else:
            logger.info("Telemetry inferred: %s", profile)

    def submit_telemetry(self, raw_json_data: str) -> None:
        """Slot called directly from JavaScript when telemetry is pushed."""
        try:
            data: TelemetryDict = self._parse_telemetry(raw_json_data)
            if self.telemetry_client is not None:
                self.telemetry_client.log(data)
            inferred_profile: DeviceProfile = self.inference_engine.analyze(data)
            self._emit_or_log_profile(inferred_profile)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error("Failed to parse incoming telemetry: %s", e)

    async def _execute_action(self, action_name: str, data: TelemetryDict) -> str:
        if action_name not in self._actions:
            return json.dumps({"status": "error", "message": f"Unsupported action: {action_name}"})
        if self.telemetry_registry is None:
            return json.dumps({"status": "error", "message": "Telemetry registry not initialized"})

        results: dict[str, dict[str, object]] = await self._actions[action_name].execute(
            self.telemetry_registry, data
        )
        return json.dumps({"status": "success", "results": results})

    async def handle_message(self, message: str) -> str:
        """Handle messages coming from the WebView (Async/Playwright style)."""
        logger.debug("Received message: %s", message)
        try:
            data = self._parse_telemetry(message)
            action_name = str(data.get("action", ""))
            return await self._execute_action(action_name, data)
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message", exc_info=True)
            return json.dumps({"status": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.exception("Error handling bridge message")
            return json.dumps({"status": "error", "message": str(e)})
