from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from osint_nexus.core import bootstrap, constants
from osint_nexus.core.evasion import EvasionWeights
from osint_nexus.core.type_defs import JSONList, JSONObject

# Guarantee directories exist at runtime before modules try to write to them
bootstrap.initialize_directories()

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
        env_parse_json=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (env_settings,)

    http_timeout: int = constants.DEFAULT_TIMEOUT
    retry_attempts: int = constants.RETRY_ATTEMPTS
    retry_backoff_factor: float = constants.BACKOFF_FACTOR
    default_rate_limit_delay: float = 0.5
    require_proxy: bool = False
    proxy_api_url: str = ""
    fingerbank_api_key: str | None = None

    # Use JSON aliases for types that might come from ENV as strings to avoid auto-json-parsing
    user_agents: list[str] | str = Field(default_factory=lambda: _DEFAULT_USER_AGENTS.copy())
    mimicry_profiles: JSONObject | str = Field(default_factory=dict)
    device_patterns: JSONList | str = Field(default_factory=list)
    dork_templates: JSONObject | str = Field(default_factory=dict)

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
    captcha: JSONObject = Field(default_factory=dict)
    service_urls: dict[str, str] = Field(
        default_factory=lambda: {
            "anti_captcha": "https://api.anti-captcha.com",
            "two_captcha": "https://2captcha.com",
            "two_captcha_res": "https://2captcha.com/res.php",
            "aparat": "https://www.aparat.com/{}",
            "github": "https://github.com/{}",
        }
    )
    tls_backend: str = "httpx"
    log_level: int = logging.INFO
    evasion_weights: EvasionWeights = Field(default_factory=EvasionWeights)

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
