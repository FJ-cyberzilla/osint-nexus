from __future__ import annotations

import asyncio
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger("osint_nexus.rate_limiter")


@runtime_checkable
class RateLimiter(Protocol):
    async def wait(self, site_name: str | None = None) -> None:
        """Call this before executing a request."""
        ...

    async def report(self, site_name: str | None, status_code: int, response_time: float) -> None:
        """Call this after the request finishes to update adaptive state."""
        ...


class AdaptiveRateLimiter:
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        # Store delays per site: {site_name: current_delay}
        self._site_delays: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def _get_delay(self, site_name: str | None) -> float:
        async with self._lock:
            if not site_name:
                return self.base_delay
            return self._site_delays.get(site_name, self.base_delay)

    async def wait(self, site_name: str | None = None) -> None:
        delay = await self._get_delay(site_name)
        logger.debug("Limiting request for %s with delay %.2fs", site_name or "global", delay)
        await asyncio.sleep(delay)

    async def report(self, site_name: str | None, status_code: int, response_time: float) -> None:
        if not site_name:
            return

        async with self._lock:
            current = self._site_delays.get(site_name, self.base_delay)

            # Adaptive logic
            if status_code == 429:
                # Exponential backoff on rate limit
                new_delay = min(current * 2.0, self.max_delay)
                logger.warning("Rate limited (429) for %s. Increasing delay to %.2fs", site_name, new_delay)
            elif status_code == 200:
                # Slight recovery when successful
                new_delay = max(current * 0.95, self.base_delay)
            elif status_code >= 500:
                # Backoff on server errors
                new_delay = min(current * 1.5, self.max_delay)
            else:
                new_delay = current

            self._site_delays[site_name] = new_delay
