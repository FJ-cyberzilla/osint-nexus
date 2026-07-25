"""
Validation logic for OSINT results.

Implements a multi-layered voting system where different rules
(content length, presence of username, exclusion of 'page not found' text)
collaborate to decide if a result is valid.
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("osint_nexus.validator")


class ValidationVote(Enum):
    VALID = "valid"
    INVALID = "invalid"
    NEUTRAL = "neutral"


class ValidationResult(BaseModel):
    """Detailed outcome of a validation check."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    details: str = ""
    rules_applied: list[str] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)


@runtime_checkable
class ValidationRule(Protocol):
    """Interface for all validation rules."""

    @property
    def name(self) -> str: ...

    def evaluate(
        self, response_text: str, platform: str, target_username: str
    ) -> tuple[ValidationVote, float]:
        """
        Evaluate response text and return a vote with confidence.
        Confidence: 0.0 to 1.0 (1.0 = absolute certainty).
        """
        ...


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


class ResultValidator:
    """
    Validates provider responses using a configurable pipeline of rules.

    Rules are evaluated independently; the final decision is:
    - VALID if at least one rule returns VALID and NO rule returns INVALID.
    - INVALID if any rule returns INVALID.
    - If no rules vote (all NEUTRAL), the result is INVALID.

    Backward‑compatible `validate()` method returns a bool.
    """

    def __init__(
        self,
        target_username: str,
        rules: list[ValidationRule] | None = None,
    ) -> None:
        self.target_username = target_username
        self._rules = rules or []
        if not self._rules:
            # Default rule set (order can affect performance but not result)
            self._rules = [
                UsernamePresenceRule(),
                ExclusionPatternRule(),
                MinimumContentLengthRule(),
            ]
        logger.info(
            "Validator initialised for '%s' with %d rules",
            target_username,
            len(self._rules),
        )

    def add_rule(self, rule: ValidationRule) -> None:
        """Append a new validation rule to the pipeline."""
        self._rules.append(rule)
        logger.debug("Rule '%s' added.", rule.name)

    def validate(self, response_text: str, platform: str) -> bool:
        """
        Quick validation returning a boolean (backward compatible).

        Args:
            response_text: The raw text content of the response.
            platform: The platform name (e.g., 'github', 'twitter').

        Returns:
            True if the username is deemed present, False otherwise.
        """
        result = self.validate_with_details(response_text, platform)
        return result.is_valid

    def _gather_votes(self, response_text: str, platform: str) -> dict[str, tuple[ValidationVote, float]]:
        votes: dict[str, tuple[ValidationVote, float]] = {}
        for rule in self._rules:
            try:
                vote, conf = rule.evaluate(response_text, platform, self.target_username)
                votes[rule.name] = (vote, conf)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Rule '%s' raised exception: %s", rule.name, exc, exc_info=True)
                votes[rule.name] = (ValidationVote.NEUTRAL, 0.0)
        return votes

    def _resolve_decision(self, votes: dict[str, tuple[ValidationVote, float]]) -> bool:
        any_valid = any(v == ValidationVote.VALID for v, _ in votes.values())
        return any_valid and not self._should_exclude(votes)

    def _should_exclude(self, votes: dict[str, tuple[ValidationVote, float]]) -> bool:
        """Determines if the result should be excluded based on exclusion rules."""
        exclusion_rules = self._get_exclusion_rules(votes)
        if not exclusion_rules:
            return False
        
        return max(conf for _, conf in exclusion_rules) > 0.98

    def _get_exclusion_rules(self, votes: dict[str, tuple[ValidationVote, float]]) -> list[tuple[str, float]]:
        """Filters votes for exclusion rules."""
        return [
            (name, conf)
            for name, (v, conf) in votes.items()
            if v == ValidationVote.INVALID and name == "ExclusionPatternRule"
        ]

    def _build_result(
        self, is_valid: bool, votes: dict[str, tuple[ValidationVote, float]]
    ) -> ValidationResult:
        if is_valid:
            avg_confidence, details = self._get_valid_result(votes)
        else:
            avg_confidence, details = self._get_invalid_result(votes)

        return ValidationResult(
            is_valid=is_valid,
            confidence=avg_confidence,
            details=details,
            rules_applied=list(votes.keys()),
            evidence={name: vote.value for name, (vote, _) in votes.items()},
        )

    def _get_valid_result(self, votes: dict[str, tuple[ValidationVote, float]]) -> tuple[float, str]:
        valid_confidences = [conf for (vote, conf) in votes.values() if vote == ValidationVote.VALID]
        avg_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.5
        details = self._format_details("Username presence confirmed by rule(s)", votes, ValidationVote.VALID)
        return avg_confidence, details

    def _get_invalid_result(self, votes: dict[str, tuple[ValidationVote, float]]) -> tuple[float, str]:
        invalid_votes = [(name, conf) for name, (v, conf) in votes.items() if v == ValidationVote.INVALID]
        if not invalid_votes:
            return 0.5, "No positive evidence found (all rules neutral)"
        
        _, highest_conf = max(invalid_votes, key=lambda x: x[1])
        details = self._format_details("Invalidated by rule(s)", votes, ValidationVote.INVALID)
        return highest_conf, details

    def _format_details(self, prefix: str, votes: dict[str, tuple[ValidationVote, float]], vote_type: ValidationVote) -> str:
        """Formats the details string for a given validation result."""
        names = [name for name, (v, _) in votes.items() if v == vote_type]
        return f"{prefix}: " + ", ".join(names)

    def validate_with_details(self, response_text: str, platform: str) -> ValidationResult:
        """
        Run all rules and return a detailed result.

        Args:
            response_text: The raw text content of the response.
            platform: The platform name (used for rule selection).

        Returns:
            A ValidationResult with the final decision and supporting data.
        """
        if not response_text:
            return ValidationResult(
                is_valid=False,
                confidence=1.0,
                details="Empty response",
                rules_applied=[],
                evidence={},
            )

        votes = self._gather_votes(response_text, platform)
        is_valid = self._resolve_decision(votes)
        return self._build_result(is_valid, votes)

    # ------------------------------------------------------------------
    # Health check (for hierarchy integration)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Validator is stateless, always healthy."""
        return True
