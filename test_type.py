from typing import TypeVar, Callable
from beartype import beartype as _beartype

_F = TypeVar("_F", bound=Callable[..., object])

# Let's see if this works
def safe_beartype(func: _F) -> _F:
    dec: Callable[[_F], _F] = _beartype  # type: ignore[assignment]
    return dec(func)
