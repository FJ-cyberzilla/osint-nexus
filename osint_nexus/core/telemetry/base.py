from abc import ABC, abstractmethod


class TelemetryProbe(ABC):
    @abstractmethod
    async def run(self) -> dict[str, object]:
        """Execute the probe and return data."""
        pass


class TelemetryExporter(ABC):
    @abstractmethod
    def export(self, data: dict[str, object]) -> None:
        """Export the collected telemetry data."""
        pass
