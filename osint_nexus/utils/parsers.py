from typing import TypeVar, cast

from beartype import beartype
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@beartype
class SafeParser:
    """Reusable type-safe dict parser for pre-Pydantic cleanup."""

    def __init__(self, data: dict[str, str | int | float | bool | None]) -> None:
        self._data = data

    def get_str(self, key: str, default: str = "") -> str:
        val = self._data.get(key)
        if isinstance(val, (str, int, float, bool)):
            return str(val)
        return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._data.get(key)
        if isinstance(val, bool):
            return val
        return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        val = self._data.get(key)
        if isinstance(val, (float, int)):
            return float(val)
        return default

    def get_int(self, key: str, default: int = 0) -> int:
        val = self._data.get(key)
        if isinstance(val, int):
            return val
        return default

    def as_model(self, model_class: type[T]) -> T:
        """Parse dict to Pydantic model using model_validate."""
        # Casting here is safe because we know our dict structure is JSON-compatible
        # And we need to satisfy strict mypy for the model_validate call.

        data_to_validate = cast(dict[str, object], self._data)
        return model_class.model_validate(data_to_validate)
