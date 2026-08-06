"""
Input sanitization utilities for OSINT Nexus.

Provides safe string cleaning to prevent injection attacks.
"""

from __future__ import annotations

import html
import logging
import re

logger = logging.getLogger("osint_nexus.security")


class SecurityUtility:
    """Collection of static security helpers for user input."""

    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """
        Sanitize user input to prevent injection.

        The input is stripped of any characters that are not alphanumeric
        or underscores, then HTML‑escaped as a defence‑in‑depth measure.

        Args:
            user_input: Raw string from an untrusted source.

        Returns:
            A safe, clean string suitable for database queries or display.
        """
        # Allow word characters (letters, digits, underscore) and periods
        sanitized = re.sub(r"[^\w\.]", "", user_input)
        # Escape HTML entities to neutralise any residual markup
        return html.escape(sanitized)

    @staticmethod
    def sanitize_for_log(log_input: str | object) -> str:
        """
        Sanitize input for logging to prevent CRLF injection (log forging).

        Replaces carriage returns and newlines with spaces.

        Args:
            log_input: The input string or object to be logged.

        Returns:
            A safe string suitable for log entries.
        """
        if not isinstance(log_input, str):
            log_input = str(log_input)
        return log_input.replace("\r", " ").replace("\n", " ")

    @staticmethod
    async def health_check() -> bool:
        """Security utility is stateless – always healthy."""
        return True
