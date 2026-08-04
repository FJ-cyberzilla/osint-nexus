import enum
from dataclasses import dataclass


class CaptchaType(enum.Enum):
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE_CAPTCHA = "image"
    CUSTOM = "custom"


@dataclass
class CaptchaSolveResult:
    token: str | None = None
    error: str | None = None
    cost: float = 0.0
    solver_name: str | None = None
    cached: bool = False

    @property
    def success(self) -> bool:
        return self.token is not None and not self.error
