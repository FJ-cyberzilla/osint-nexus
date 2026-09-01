from collections.abc import Mapping

from beartype import beartype

from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.type_defs import JSONValue


class FingerprintStrategyRegistry:
    """Registry to manage and retrieve fingerprinting strategies."""

    def __init__(self) -> None:
        self._strategies: dict[
            str, FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]
        ] = {}

    @beartype
    def register(
        self, strategy: FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]
    ) -> None:
        """Register a new strategy."""
        self._strategies[strategy.name] = strategy

    @beartype
    def get_all(self) -> list[FingerprintStrategy[Mapping[str, JSONValue], Mapping[str, JSONValue]]]:
        """Get all registered strategies."""
        return list(self._strategies.values())
