"""Project-wide constants for OSINT Nexus."""

from typing import Final

VERSION: Final[str] = "2.0.0"

COLOR_ORANGE: Final[str] = "bold orange1"
COLOR_TIP: Final[str] = "yellow"
JITTER_MIN: Final[float] = 1.0
JITTER_MAX: Final[float] = 3.0

DEFAULT_TIMEOUT: Final[int] = 10
RETRY_ATTEMPTS: Final[int] = 3
BACKOFF_FACTOR: Final[float] = 0.5
