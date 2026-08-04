from __future__ import annotations

from dataclasses import dataclass, field

from osint_nexus.core.config import Config


@dataclass
class CaptchaConfig:
    """Configuration for CAPTCHA solving."""

    two_captcha_key: str | None = None
    anti_captcha_key: str | None = None
    request_timeout: float = 30.0
    solve_timeout: float = 120.0
    poll_interval: float = 2.0
    max_cost_per_solve: float = 0.05
    daily_budget: float = 1.0
    cost_tracking: bool = True
    cache_ttl: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    solver_priority: list[str] = field(default_factory=lambda: ["2captcha", "anti_captcha"])

    @classmethod
    def from_config(cls, config: Config) -> CaptchaConfig:
        captcha_cfg = config.get("captcha", {})
        return cls(
            two_captcha_key=captcha_cfg.get("two_captcha_key"),
            anti_captcha_key=captcha_cfg.get("anti_captcha_key"),
            request_timeout=captcha_cfg.get("request_timeout", 30.0),
            solve_timeout=captcha_cfg.get("solve_timeout", 120.0),
            max_cost_per_solve=captcha_cfg.get("max_cost_per_solve", 0.05),
            daily_budget=captcha_cfg.get("daily_budget", 1.0),
            cache_ttl=captcha_cfg.get("cache_ttl", 300),
            max_retries=captcha_cfg.get("max_retries", 3),
            retry_delay=captcha_cfg.get("retry_delay", 1.0),
        )
