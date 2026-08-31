from typing import Protocol, TypeVar, runtime_checkable

from beartype import beartype

from collections.abc import Mapping
from osint_nexus.core.type_defs import JSONValue, JSONObject

T_Data = TypeVar("T_Data", contravariant=True, bound=JSONValue | Mapping[str, JSONValue])
T_Result = TypeVar("T_Result", covariant=True, bound=Mapping[str, JSONValue])


@runtime_checkable
class FingerprintStrategy(Protocol[T_Data, T_Result]):
    """Protocol for all fingerprinting strategies."""

    name: str

    @beartype
    def extract(self, data: T_Data) -> T_Result:
        """Extract fingerprint from given data."""
        ...


class BaseDetector(Protocol):
    """Base protocol for novel detectors."""

    name: str

    @beartype
    async def analyze(self, data: JSONObject) -> float:
        """Analyze data and return evasion probability."""
        ...
