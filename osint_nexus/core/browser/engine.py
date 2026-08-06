from typing import Protocol, runtime_checkable


@runtime_checkable
class BrowserEngineProtocol(Protocol):
    async def run_navigation(self, url: str) -> None:
        """Navigate to the specified URL."""
