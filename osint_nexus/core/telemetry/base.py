from abc import ABC, abstractmethod
from typing import Any


class TelemetryProbe(ABC):
    @abstractmethod
    async def run(self) -> dict[str, Any]:
        """Execute the probe and return data."""
        pass


class TelemetryExporter(ABC):
    @abstractmethod
    def export(self, data: dict[str, Any]) -> None:
        """Export the collected telemetry data."""
        pass
