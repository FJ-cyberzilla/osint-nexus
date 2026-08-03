from __future__ import annotations

import re

from osint_nexus.core.validators.base import ValidationVote


class UsernamePresenceRule:
    """Rule that checks if the username literally appears in the response."""

    name = "UsernamePresenceRule"

    def evaluate(
        self, response_text: str, platform: str, target_username: str
    ) -> tuple[ValidationVote, float]:
        if not response_text or not target_username:
            return ValidationVote.NEUTRAL, 0.0

        if target_username.lower() in response_text.lower():
            return ValidationVote.VALID, 0.8
        return ValidationVote.NEUTRAL, 0.0


class ExclusionPatternRule:
    """Rule that checks for known 'Not Found' or 'Error' signatures."""

    def __init__(self, patterns: list[str] | None = None, name: str | None = None) -> None:
        self.name = name or "ExclusionPatternRule"
        self._patterns = patterns or [
            r"404 Not Found",
            r"page not found",
            r"doesn't exist",
            r"user not found",
            r"could not find",
            r"profile not found",
            r"no results found",
        ]
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]

    def evaluate(
        self, response_text: str, platform: str, target_username: str
    ) -> tuple[ValidationVote, float]:
        for pattern in self._compiled:
            if pattern.search(response_text):
                return ValidationVote.INVALID, 0.95
        return ValidationVote.NEUTRAL, 0.0


class MinimumContentLengthRule:
    """Rule that flags very short responses as potentially invalid."""

    name = "MinimumContentLengthRule"

    def __init__(self, min_length: int = 50, max_length: int = 1_000_000) -> None:
        self.min_length = min_length
        self.max_length = max_length

    def evaluate(
        self, response_text: str, platform: str, target_username: str
    ) -> tuple[ValidationVote, float]:
        length = len(response_text)
        if length < self.min_length:
            return ValidationVote.INVALID, 0.9
        if length > self.max_length:
            # Unusually large – treat as suspicious but not necessarily invalid
            return ValidationVote.NEUTRAL, 0.3
        return ValidationVote.NEUTRAL, 0.0
