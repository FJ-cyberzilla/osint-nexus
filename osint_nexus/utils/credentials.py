from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv, set_key


class CredentialManager:
    """Securely manages sensitive credentials in a .env file."""

    def __init__(self, env_path: str | Path = ".env"):
        self.env_path = Path(env_path)
        if not self.env_path.exists():
            self.env_path.touch()
        load_dotenv(dotenv_path=self.env_path)

    def get_credential(self, key: str) -> str | None:
        """Retrieves a credential from the environment."""
        return os.getenv(key)

    def set_credential(self, key: str, value: str) -> None:
        """Sets and persists a credential in the .env file."""
        set_key(dotenv_path=self.env_path, key_to_set=key, value_to_set=value)
        # Update the current environment
        os.environ[key] = value
