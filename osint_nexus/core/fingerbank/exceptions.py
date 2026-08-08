from __future__ import annotations


class FingerbankError(Exception):
    """Base exception for Fingerbank API."""

    pass


class FingerbankUnauthorizedError(FingerbankError):
    """401 Unauthorized."""

    pass


class FingerbankForbiddenError(FingerbankError):
    """403 Forbidden."""

    pass


class FingerbankRateLimitedError(FingerbankError):
    """429 Rate limited."""

    pass


class FingerbankBackendError(FingerbankError):
    """502 Backend error."""

    pass


class FingerbankNotFoundError(FingerbankError):
    """404 Device not found."""

    pass
