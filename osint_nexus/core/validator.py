"""
Advanced result validation for OSINT username checks.

Uses a pluggable rule engine to assess whether a provider's response
genuinely indicates the presence of a target username. Rules can be
platform‑specific, combining positive signals (username found) and
negative signals (error messages, "not found" pages) for high accuracy.
"""
from __future__ import annotations

import enum
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("osint_nexus.validator")


class ValidationVote(enum.Enum):
    """Vote cast by a single validation rule."""
    VALID = "valid"          # positive evidence for username presence
    INVALID = "invalid"      # evidence that username is NOT present
    NEUTRAL = "neutral"      # rule does not apply or is inconclusive


@dataclass
class ValidationResult:
    """
    Encapsulates the outcome of a validation check.

    Attributes:
        is_valid: Overall decision – True if username is considered present.
        confidence: 0.0 to 1.0 indicating confidence in the decision.
        details: Human‑readable explanation of why the result was reached.
        rules_applied: Names of rules that contributed to the decision.
        evidence: Dict of rule name -> vote for transparency.
    """
    is_valid: bool
    confidence: float = 1.0
    details: str = ""
    rules_applied: List[str] = field(default_factory=list)
    evidence: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"ValidationResult(valid={self.is_valid}, confidence={self.confidence:.2f})"


class ValidationRule(ABC):
    """
    Abstract base class for a single validation check.

    Subclasses must implement `evaluate`. They return a `ValidationVote`
    and, optionally, a confidence score (0–1) for that specific vote.
    """

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__

    @abstractmethod
    def evaluate(self, response_text: str, platform: str, username: str) -> tuple[ValidationVote, float]:
        """
        Assess the response and return a (vote, confidence) tuple.

        Args:
            response_text: The HTTP response body (or snippet).
            platform: The name of the platform being checked.
            username: The target username.

        Returns:
            A tuple of (ValidationVote, confidence).
            Confidence should be between 0.0 and 1.0.
        """
        ...


class UsernamePresenceRule(ValidationRule):
    """Checks for the literal presence of the target username (case‑insensitive)."""

    def evaluate(self, response_text: str, platform: str, username: str) -> tuple[ValidationVote, float]:
        if not username:
            return ValidationVote.NEUTRAL, 0.0
        pattern = re.compile(re.escape(username), re.IGNORECASE)
        if pattern.search(response_text):
            return ValidationVote.VALID, 0.9  # moderately high confidence
        return ValidationVote.INVALID, 0.7


class ExclusionPatternRule(ValidationRule):
    """
    Detects known "not found" or error patterns that indicate the
    username is *not* present, even if it appears elsewhere in the page.
    """

    # Default patterns – extend per platform
    DEFAULT_PATTERNS: Dict[str, List[str]] = {
        "generic": [
            r"not\s*found",
            r"doesn['’]t\s*exist",
            r"no\s*results",
            r"page\s*not\s*available",
            r"user\s*not\s*found",
            r"profile\s*not\s*found",
            r"nothing\s*here",
        ],
        "github": [
            r"is\s*not\s*a\s*user",
            r"could\s*not\s*find\s*user",
        ],
    }

    def __init__(
        self,
        name: str = "ExclusionPatternRule",
        platform_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        super().__init__(name)
        self._patterns = platform_patterns or self.DEFAULT_PATTERNS

    def evaluate(self, response_text: str, platform: str, username: str) -> tuple[ValidationVote, float]:
        # Get patterns for this platform, falling back to generic
        patterns = self._patterns.get(platform, self._patterns.get("generic", []))
        for pat in patterns:
            if re.search(pat, response_text, re.IGNORECASE):
                return ValidationVote.INVALID, 0.95  # high confidence this is a "not found" page
        return ValidationVote.NEUTRAL, 0.0


class MinimumContentLengthRule(ValidationRule):
    """
    Rejects responses that are too short (likely error pages or empty
    responses) and raises a flag if the content is unusually large.
    """

    def __init__(
        self,
        name: str = "MinimumContentLengthRule",
        min_length: int = 100,
        max_length: int = 5_000_000,
    ) -> None:
        super().__init__(name)
        self.min_length = min_length
        self.max_length = max_length

    def evaluate(self, response_text: str, platform: str, username: str) -> tuple[ValidationVote, float]:
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
        rules: Optional[List[ValidationRule]] = None,
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

    def validate_with_details(
        self, response_text: str, platform: str
    ) -> ValidationResult:
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

        votes: Dict[str, tuple[ValidationVote, float]] = {}
        any_valid = False
        any_invalid = False

        for rule in self._rules:
            try:
                vote, conf = rule.evaluate(response_text, platform, self.target_username)
                votes[rule.name] = (vote, conf)
                if vote == ValidationVote.VALID:
                    any_valid = True
                elif vote == ValidationVote.INVALID:
                    any_invalid = True
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "Rule '%s' raised exception: %s", rule.name, exc, exc_info=True
                )
                votes[rule.name] = (ValidationVote.NEUTRAL, 0.0)

        # Decision logic
        # Prioritize VALID votes. 
        # Only reject if ExclusionPatternRule is extremely high confidence 
        # AND no VALID vote exists.

        is_valid = any_valid
        if any_valid:
             # If we found the username, check if any EXTREMELY high-confidence 
             # exclusion rule invalidates it.
             exclusion_rules = [
                (name, conf) for name, (v, conf) in votes.items() 
                if v == ValidationVote.INVALID and name == "ExclusionPatternRule"
            ]
             if exclusion_rules:
                 highest_exclusion_conf = max(conf for _, conf in exclusion_rules)
                 if highest_exclusion_conf > 0.98:
                     is_valid = False
        else:
            # If no VALID vote, check if any rule invalidates it
            if any_invalid:
                is_valid = False

        if is_valid:
            # Confidence: average of all VALID vote confidences (skip NEUTRAL/INVALID)
            valid_confidences = [
                conf for (vote, conf) in votes.values() if vote == ValidationVote.VALID
            ]
            avg_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.5
            details = "Username presence confirmed by rule(s): " + ", ".join(
                name for name, (v, _) in votes.items() if v == ValidationVote.VALID
            )
        else:
            # If invalid due to an INVALID vote, confidence is that rule's confidence
            invalid_votes = [
                (name, conf) for name, (v, conf) in votes.items() if v == ValidationVote.INVALID
            ]
            if invalid_votes:
                _, highest_conf = max(invalid_votes, key=lambda x: x[1])
                avg_confidence = highest_conf
                details = "Invalidated by rule(s): " + ", ".join(
                    name for name, (v, _) in votes.items() if v == ValidationVote.INVALID
                )
            else:
                avg_confidence = 0.5
                details = "No positive evidence found (all rules neutral)"

        return ValidationResult(
            is_valid=is_valid,
            confidence=avg_confidence,
            details=details,
            rules_applied=list(votes.keys()),
            evidence={name: vote.value for name, (vote, _) in votes.items()},
        )

    # ------------------------------------------------------------------
    # Health check (for hierarchy integration)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Validator is stateless, always healthy."""
        return True
