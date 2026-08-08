from typing import Any

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy


class FingerprintStrategyRegistry:
    """Registry to manage and retrieve fingerprinting strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, FingerprintStrategy[Any, Any]] = {}

    @beartype
    def register(self, strategy: FingerprintStrategy[Any, Any]) -> None:
        """Register a new strategy."""
        self._strategies[strategy.name] = strategy

    @beartype
    def get_all(self) -> list[FingerprintStrategy[Any, Any]]:
        """Get all registered strategies."""
        return list(self._strategies.values())
