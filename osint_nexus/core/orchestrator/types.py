from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from osint_nexus.core.extractor import PivotExtractor
    from osint_nexus.core.mimicry import HumanMimicryEngine
    from osint_nexus.core.provider_types import (
        DatabaseManagerProtocol,
        ValidatorProtocol,
    )
    from osint_nexus.utils.network import NetworkManager


@runtime_checkable
class HealthCheckProtocol(Protocol):
    async def is_healthy(self) -> bool: ...


@dataclass(frozen=True)
class OrchestratorDeps:
    """Container for core service dependencies to reduce orchestrator bloat."""

    health: HealthCheckProtocol
    validator: ValidatorProtocol
    db_manager: DatabaseManagerProtocol
    network: NetworkManager
    mimicry: HumanMimicryEngine
    extractor: PivotExtractor
