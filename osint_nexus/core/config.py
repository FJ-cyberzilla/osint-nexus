"""Centralised configuration for OSINT Nexus."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from osint_nexus.core import constants

logger = logging.getLogger("osint_nexus.config")

_DEFAULT_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

@dataclass
class Config:
    http_timeout: int = constants.DEFAULT_TIMEOUT
    retry_attempts: int = constants.RETRY_ATTEMPTS
    retry_backoff_factor: float = constants.BACKOFF_FACTOR
    default_rate_limit_delay: float = 0.5
    require_proxy: bool = False
    proxy_api_url: str = ""
    user_agents: List[str] = field(default_factory=lambda: _DEFAULT_USER_AGENTS.copy())
    min_jitter: float = constants.JITTER_MIN
    max_jitter: float = constants.JITTER_MAX
    typing_char_min: float = 0.05
    typing_char_max: float = 0.3
    typing_pause_every: int = 8
    typing_pause_extra: float = 0.5
    think_base: float = 1.5
    click_hesitation_prob: float = 0.4
    click_misclick_prob: float = 0.08
    click_observation_delay: Tuple[float, float] = (0.5, 2.0)
    mimicry_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    db_path: str = "osint_results.db"
    device_patterns: List[Tuple[str, str, str]] = field(default_factory=list)
    captcha_api_key: str = ""
    dork_templates: Dict[str, List[str]] = field(default_factory=dict)
    tls_backend: str = "httpx"
    log_level: int = logging.INFO

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    @classmethod
    def from_env(cls, **overrides: Any) -> Config:
        instance = cls()
        for field_name in cls.__dataclass_fields__:
            env_var = f"OSINT_{field_name.upper()}"
            if env_var in os.environ:
                raw = os.environ[env_var]
                target_type = type(getattr(instance, field_name))
                try:
                    if target_type is bool:
                        setattr(instance, field_name, raw.lower() in ("1","true","yes"))
                    elif target_type is int:
                        setattr(instance, field_name, int(raw))
                    elif target_type is float:
                        setattr(instance, field_name, float(raw))
                    elif target_type is list or target_type is tuple:
                        setattr(instance, field_name, json.loads(raw))
                    elif target_type is dict:
                        setattr(instance, field_name, json.loads(raw))
                    else:
                        setattr(instance, field_name, raw)
                except (ValueError, json.JSONDecodeError):
                    logger.warning("Invalid env value for %s", env_var)
        for k, v in overrides.items():
            if hasattr(instance, k):
                setattr(instance, k, v)
        return instance

    @classmethod
    def from_file(cls, path: str | Path) -> Config:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        instance = cls()
        for k, v in data.items():
            if hasattr(instance, k):
                setattr(instance, k, v)
        return instance
