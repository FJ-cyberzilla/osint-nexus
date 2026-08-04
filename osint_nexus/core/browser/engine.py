from abc import ABC, abstractmethod


class BrowserEngine(ABC):
    @abstractmethod
    def run_navigation(self, url: str) -> None:
        pass
