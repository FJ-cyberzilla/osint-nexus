from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from playwright.async_api import Page
else:
    Page = Any


@runtime_checkable
class BrowserContextProtocol(Protocol):
    async def add_init_script(self, script: str) -> None: ...
    async def new_page(self) -> Page: ...
    async def close(self) -> None: ...
    @property
    def pages(self) -> list[Page]: ...


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
