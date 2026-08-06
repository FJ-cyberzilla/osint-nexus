from typing import Protocol, runtime_checkable


@runtime_checkable
class PageProtocol(Protocol):
    async def close(self) -> None: ...
    async def goto(self, url: str) -> None: ...
    async def content(self) -> str: ...


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
    async def new_context(
        self,
        *,
        user_agent: str | None = None,
        viewport: dict[str, int] | None = None,
        proxy: dict[str, str] | None = None,
        extra_http_headers: dict[str, str] | None = None,
        bypass_csp: bool = False,
    ) -> BrowserContextProtocol: ...
