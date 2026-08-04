from typing import Any

from .base import TelemetryProbe


class TelemetryRegistry:
    def __init__(self) -> None:
        self._probes: dict[str, TelemetryProbe] = {}

    def register_probe(self, name: str, probe: TelemetryProbe) -> None:
        self._probes[name] = probe

    async def run_all(self) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        for name, probe in self._probes.items():
            results[name] = await probe.run()
        return results
