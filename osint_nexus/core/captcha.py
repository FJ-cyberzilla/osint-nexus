"""
Advanced captcha solving module for OSINT Nexus.

Supports multiple captcha types (reCAPTCHA v2, v3, hCaptcha, Cloudflare
Turnstile, etc.) and multiple solving backends (2captcha, Anti‑Captcha,
custom solvers) via a registry-based architecture. All solving is
asynchronous and includes health‑check capabilities.
"""

from __future__ import annotations

import asyncio
import enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("osint_nexus.captcha")


class CaptchaType(enum.Enum):
    """
    Enumeration of supported captcha challenges.

    Attributes:
        RECAPTCHA_V2: Standard "I'm not a robot" checkbox.
        RECAPTCHA_V3: Invisible, score‑based reCAPTCHA.
        HCAPTCHA: hCaptcha challenge.
        TURNSTILE: Cloudflare Turnstile.
        IMAGE_CAPTCHA: Classic text‑in‑image captcha.
        CUSTOM: Any other captcha type (use a descriptive string).
    """

    RECAPTCHA_V2 = "captcha"
    RECAPTCHA_V3 = "captcha2"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE_CAPTCHA = "image"
    CUSTOM = "custom"


class CaptchaSolveResult:
    """
    Result of a captcha solve attempt.

    Attributes:
        token: The solution token, or None if solving failed.
        error: Error description if solving was unsuccessful.
        cost: Estimated cost (in USD) if using a paid service.
    """

    def __init__(
        self,
        token: str | None = None,
        error: str | None = None,
        cost: float = 0.0,
    ) -> None:
        self.token = token
        self.error = error
        self.cost = cost

    @property
    def success(self) -> bool:
        """True if a valid token was obtained."""
        return self.token is not None and not self.error


class CaptchaSolver(ABC):
    """
    Abstract base class for all captcha solving backends.

    Subclasses must implement `solve`. Optional methods
    `is_supported` and `health_check` allow dynamic discovery
    and integration with the hierarchy manager.
    """

    def is_supported(self, captcha_type: CaptchaType) -> bool:
        """
        Check if this solver can handle the given captcha type.

        Override in subclasses to filter solver selection.
        """
        return True  # by default all types are considered supported

    @abstractmethod
    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        **kwargs,
    ) -> CaptchaSolveResult:
        """
        Solve a captcha challenge.

        Args:
            site_key: Public key of the captcha.
            url: URL of the page containing the captcha.
            captcha_type: Type of captcha (default RECAPTCHA_V2).
            **kwargs: Additional parameters (e.g., action for v3, data-s for hCaptcha).

        Returns:
            CaptchaSolveResult with the token or error details.
        """
        ...

    async def health_check(self) -> bool:
        """
        Perform a quick health check of the solver.

        Returns True if the backend is responsive and functional.
        """
        return True  # default: assume healthy if not overridden


class MockCaptchaSolver(CaptchaSolver):
    """
    A mock solver for testing and development.

    Returns a dummy token after a short delay. Useful when real solving
    is not needed or when running integration tests.
    """

    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        **kwargs,
    ) -> CaptchaSolveResult:
        """Simulate captcha solving with a delay."""
        logger.debug("Mock solving %s for %s", captcha_type.value, url)
        await asyncio.sleep(0.1)  # simulate work
        return CaptchaSolveResult(
            token="mock_token_abc123",
            cost=0.0,
        )


class CaptchaSolverRegistry:
    """
    Registry for multiple captcha solving backends.

    Allows dynamic selection of the best solver for a given captcha type
    based on availability and support.
    """

    def __init__(self) -> None:
        self._solvers: dict[str, CaptchaSolver] = {}

    def register(self, name: str, solver: CaptchaSolver) -> None:
        """
        Register a solver instance under a unique name.

        Args:
            name: Identifier for the solver (e.g., "2captcha").
            solver: Instance of a CaptchaSolver subclass.
        """
        self._solvers[name] = solver
        logger.info("Captcha solver '%s' registered.", name)

    def unregister(self, name: str) -> None:
        """Remove a solver from the registry."""
        if name in self._solvers:
            del self._solvers[name]
            logger.info("Captcha solver '%s' unregistered.", name)

    def get_solver(self, name: str) -> CaptchaSolver | None:
        """Return a solver by name, or None if not found."""
        return self._solvers.get(name)

    def find_solver(self, captcha_type: CaptchaType, exclude: list | None = None) -> CaptchaSolver | None:
        """
        Find the first available solver that supports the captcha type.

        Args:
            captcha_type: The type of captcha to solve.
            exclude: Optional list of solver names to skip.

        Returns:
            A solver instance, or None if no suitable solver found.
        """
        exclude = exclude or []
        for name, solver in self._solvers.items():
            if name in exclude:
                continue
            if solver.is_supported(captcha_type):
                return solver
        return None

    async def solve(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType = CaptchaType.RECAPTCHA_V2,
        solver_name: str | None = None,
        **kwargs,
    ) -> CaptchaSolveResult:
        """
        Solve a captcha using a specific solver or the first available.

        Args:
            site_key: Public captcha key.
            url: Page URL.
            captcha_type: Type of captcha.
            solver_name: If given, use this specific solver; otherwise use best match.
            **kwargs: Additional parameters passed to solver.

        Returns:
            CaptchaSolveResult with the token or failure info.
        """
        solver = self.get_solver(solver_name) if solver_name else self.find_solver(captcha_type)
        if not solver:
            return CaptchaSolveResult(error=f"No solver available for {captcha_type.value}")
        try:
            result = await solver.solve(
                site_key=site_key,
                url=url,
                captcha_type=captcha_type,
                **kwargs,
            )
            return result
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Captcha solving failed: %s", exc, exc_info=True)
            return CaptchaSolveResult(error=str(exc))

    def list_solvers(self) -> dict[str, bool]:
        """Return a dict of solver names and their support status."""
        return dict.fromkeys(self._solvers, True)
