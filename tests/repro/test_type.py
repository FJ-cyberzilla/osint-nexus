from collections.abc import Callable
from typing import TypeVar

from beartype import beartype as _beartype

_F = TypeVar("_F", bound=Callable[..., object])


# Let's see if this works
def safe_beartype[F: Callable[..., object]](func: F) -> F:
    dec: Callable[[F], F] = _beartype  # type: ignore[assignment]
    return dec(func)
