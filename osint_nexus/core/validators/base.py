from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class ValidationVote(Enum):
    VALID = "valid"
    INVALID = "invalid"
    NEUTRAL = "neutral"


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


class ValidationResult(BaseModel):
    """Detailed outcome of a validation check."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    confidence: float = Field(ge=0.0, le=1.0)
    details: str = ""
    rules_applied: list[str] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)
