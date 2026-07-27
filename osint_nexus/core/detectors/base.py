from abc import ABC, abstractmethod
from typing import Any


class BaseDetector(ABC):
    """Abstract base class for all detection techniques."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the detector."""
        pass

    @abstractmethod
    async def analyze(self, telemetry: Any) -> float:
        """Analyze telemetry data and return a detection score [0.0, 1.0]."""
        pass
