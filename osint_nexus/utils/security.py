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
        # Allow only word characters (letters, digits, underscore)
        sanitized = re.sub(r"[^\w]", "", user_input)
        # Escape HTML entities to neutralise any residual markup
        return html.escape(sanitized)

    @staticmethod
    async def health_check() -> bool:
        """Security utility is stateless – always healthy."""
        return True
