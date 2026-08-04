"""
Session and Cookie Manager.

Maintains an encrypted pool of authenticated session tokens and cookies
for restricted platforms.
"""

from __future__ import annotations

import json
import logging
import os

from osint_nexus.core.exceptions import DatabaseError

logger = logging.getLogger("osint_nexus.core.sessions")

# Define a more specific type for session data
type SessionData = dict[str, str | int | float | bool]


class SessionManager:
    """
    Manages encrypted authentication credentials.
    """

    def __init__(self, storage_path: str = "data/sessions.json") -> None:
        self.storage_path = storage_path
        self._sessions: dict[str, SessionData] = {}
        self._load_sessions()

    def _load_sessions(self) -> None:
        """Loads sessions from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path) as f:
                    self._sessions = json.load(f)
                logger.info("Loaded %d sessions from %s.", len(self._sessions), self.storage_path)
            except (OSError, json.JSONDecodeError) as e:
                logger.error("Failed to load sessions: %s", e)
                raise DatabaseError(f"Failed to load sessions from {self.storage_path}") from e
        else:
            logger.debug("No session storage found at %s.", self.storage_path)

    def get_session(self, platform: str) -> SessionData | None:
        """Retrieves session data for a platform."""
        session = self._sessions.get(platform)
        if session:
            logger.info("Retrieved session for platform: %s", platform)
        else:
            logger.debug("No session found for platform: %s", platform)
        return session

    def save_session(self, platform: str, data: SessionData) -> None:
        """Saves session data."""
        logger.info("Saving session data for platform: %s", platform)
        self._sessions[platform] = data
        self._save_to_disk()

    def _save_to_disk(self) -> None:
        """Persists sessions to disk."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(self._sessions, f)
        logger.info("Sessions saved.")
