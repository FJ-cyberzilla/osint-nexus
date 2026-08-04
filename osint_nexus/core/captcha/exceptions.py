class CaptchaError(Exception):
    """Base CAPTCHA exception."""


class CaptchaTimeoutError(CaptchaError):
    """Solving took longer than allowed."""


class CaptchaBudgetExceeded(CaptchaError):
    """Cost limit or daily budget exceeded."""


class CaptchaServiceError(CaptchaError):
    """API error from the solving service."""
