"""Centralised configuration for OSINT Nexus."""

from __future__ import annotations

import json
import logging
from dataclasses import field
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from osint_nexus.core import constants
from osint_nexus.core.evasion import EvasionWeights

# Locate the project root (assumes config.py is inside osint_nexus/core/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Define standard storage paths
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Guarantee directories exist at runtime before modules try to write to them
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Exported absolute file paths for database and logging subsystems
DATABASE_PATH = DATA_DIR / "osint_results.db"
LOG_FILE_PATH = LOGS_DIR / "osint.log"

logger = logging.getLogger("osint_nexus.config")

_DEFAULT_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OSINT_",
        env_nested_delimiter="__",
        # We handle complex types manually to avoid pydantic-settings auto-parsing crashes
    )

    http_timeout: int = constants.DEFAULT_TIMEOUT
    retry_attempts: int = constants.RETRY_ATTEMPTS
    retry_backoff_factor: float = constants.BACKOFF_FACTOR
    default_rate_limit_delay: float = 0.5
    require_proxy: bool = False
    proxy_api_url: str = ""

    # Use Any for types that might come from ENV as strings to avoid auto-json-parsing
    user_agents: Any = Field(default_factory=lambda: _DEFAULT_USER_AGENTS.copy())
    mimicry_profiles: Any = Field(default_factory=dict)
    device_patterns: Any = Field(default_factory=list)
    dork_templates: Any = Field(default_factory=dict)

    min_jitter: float = constants.JITTER_MIN
    max_jitter: float = constants.JITTER_MAX
    typing_char_min: float = 0.05
    typing_char_max: float = 0.3
    typing_pause_every: int = 8
    typing_pause_extra: float = 0.5
    think_base: float = 1.5
    click_hesitation_prob: float = 0.4
    click_misclick_prob: float = 0.08
    click_observation_delay: tuple[float, float] = (0.5, 2.0)
    db_path: str = "osint_results.db"
    captcha: dict[str, Any] = Field(default_factory=dict)
    tls_backend: str = "httpx"
    log_level: int = logging.INFO
    evasion_weights: EvasionWeights = field(default_factory=EvasionWeights)

    @field_validator("user_agents", "mimicry_profiles", "device_patterns", "dork_templates", mode="before")
    @classmethod
    def validate_json_fields(cls, v: Any, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid value for %s, using default.", info.field_name)
                # Return the default value for the field
                if info.field_name == "user_agents":
                    return _DEFAULT_USER_AGENTS.copy()
                if info.field_name == "device_patterns":
                    return []
                return {}
        return v

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    @classmethod
    def from_env(cls, **overrides: Any) -> Config:
        return cls(**overrides)

    @classmethod
    def from_file(cls, path: str | Path) -> Config:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


def get_config() -> Config:
    return Config()
