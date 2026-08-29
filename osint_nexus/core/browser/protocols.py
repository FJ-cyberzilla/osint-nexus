from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, Protocol, TypeVar, runtime_checkable

_P = ParamSpec("_P")
_R = TypeVar("_R")


@runtime_checkable
class PageProtocol(Protocol):
    async def close(self) -> None: ...
    async def goto(self, url: str) -> None: ...
    async def content(self) -> str: ...
    async def expose_function(self, name: str, callback: Callable[_P, _R]) -> None: ...


@runtime_checkable
class BrowserContextProtocol(Protocol):
    async def add_init_script(self, script: str) -> None: ...
    async def new_page(self) -> PageProtocol: ...
    async def close(self) -> None: ...
    @property
    def pages(self) -> list[PageProtocol]: ...


@runtime_checkable
class BrowserProtocol(Protocol):
    def is_connected(self) -> bool: ...
    async def close(self) -> None: ...
    async def new_context(
        self,
        *,
        user_agent: str | None = None,
        viewport: dict[str, int] | None = None,
        proxy: dict[str, str] | None = None,
        extra_http_headers: dict[str, str] | None = None,
        bypass_csp: bool = False,
    ) -> BrowserContextProtocol: ...


@runtime_checkable
class ChromiumProtocol(Protocol):
    async def launch(self, *, headless: bool = False, args: list[str] | None = None) -> BrowserProtocol: ...


@runtime_checkable
class PlaywrightProtocol(Protocol):
    @property
    def chromium(self) -> ChromiumProtocol: ...
    async def stop(self) -> None: ...
    async def start(self) -> PlaywrightProtocol: ...
