from .base import (
    CaptchaBudgetExceeded,
    CaptchaConfig,
    CaptchaError,
    CaptchaServiceError,
    CaptchaSolver,
    CaptchaSolveResult,
    CaptchaTimeoutError,
    CaptchaType,
)
from .registry import CaptchaSolverRegistry, create_captcha_registry
