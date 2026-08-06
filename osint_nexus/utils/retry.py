"""
Asynchronous retry handler with exponential backoff and jitter.

Provides a configurable retry loop for network operations and other
transient failures. Integrates with the project's Config class.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.retry")

T = TypeVar("T")
P = ParamSpec("P")


class RetryHandler:
    """
    Retries an async callable with exponential backoff and full jitter.

    Configurable via the project's Config object (retry_attempts,
    retry_backoff_factor). Catches a configurable tuple of exception types;
    by default all subclasses of Exception.

    Usage:
        handler = RetryHandler(config)
        result = await handler.run(my_async_func, arg1, arg2)
    """

    def __init__(
        self,
        config: Config,
        *,
        retry_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> None:
        self.config = config
        self.retry_exceptions = retry_exceptions

    async def run(
        self,
        func: Callable[P, Awaitable[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """
        Execute *func* with retries.

        Args:
            func: Async callable.
            *args: Positional arguments for *func*.
            **kwargs: Keyword arguments for *func*.

        Returns:
            The return value of *func* on success.

        Raises:
            The last exception if all retries are exhausted.
        """
        max_attempts = self.config.retry_attempts
        backoff = self.config.retry_backoff_factor
        last_exception: BaseException | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except self.retry_exceptions as exc:
                last_exception = exc
                if attempt == max_attempts:
                    logger.error(
                        "All %d retries exhausted. Last error: %s",
                        max_attempts,
                        exc,
                    )
                    raise
                # Exponential backoff with full jitter
                delay = backoff * (2 ** (attempt - 1)) * random.uniform(0.5, 1.5)
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.2fs...",
                    attempt,
                    max_attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
        # Should never reach here; fallback raise
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry loop finished without result or exception")

    async def health_check(self) -> bool:
        """Always healthy (stateless)."""
        return True
