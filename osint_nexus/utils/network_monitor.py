from osint_nexus.core.config import Config
from osint_nexus.core.evasion_agent import EvasionAgent


class NetworkMonitor:
    """Monitors environment and manages response status."""

    def __init__(self, config: Config, evasion: EvasionAgent) -> None:
        self.config = config
        self.evasion = evasion
        self.dynamic_timeout: float = float(config.http_timeout)

    def adapt(self, response_time: float) -> None:
        if response_time > (self.dynamic_timeout * 0.8):
            new_timeout = min(self.dynamic_timeout * 1.5, float(self.config.http_timeout * 2.5))
            if new_timeout != self.dynamic_timeout:
                self.dynamic_timeout = new_timeout

    async def handle_status(self, status_code: int) -> None:
        if status_code in (403, 429, 401, 407):
            await self.evasion.report_failure(status_code)
            self.dynamic_timeout = min(self.dynamic_timeout * 1.2, float(self.config.http_timeout * 3))
