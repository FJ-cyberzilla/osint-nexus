from osint_nexus.core.validator import ResultValidator
from osint_nexus.core.validators.base import ValidationVote
from osint_nexus.core.validators.rules import ExclusionPatternRule


def test_validation_logic_permissive() -> None:
    # Setup validator with default rules
    validator = ResultValidator(target_username="testuser")

    # Simulate a page that contains both the username AND an error/exclusion pattern
    # With the fix, this should be valid because UsernamePresenceRule returns VALID
    # and the exclusion pattern confidence is not > 0.98.
    response_text = "Profile for testuser not found"
    platform = "generic"

    # UsernamePresenceRule should find 'testuser' -> VALID
    # ExclusionPatternRule should find 'not found' -> INVALID

    result = validator.validate_with_details(response_text, platform)

    assert result.is_valid is True
    assert result.evidence["UsernamePresenceRule"] == "valid"
    assert result.evidence["ExclusionPatternRule"] == "invalid"


def test_validation_logic_high_confidence_exclusion() -> None:
    # Setup validator
    validator = ResultValidator(target_username="testuser")

    # Simulate a page that is definitely not found (high confidence exclusion)
    # I need to mock/craft a response that triggers high confidence exclusion
    # The default exclusion pattern rule does not specify confidence, it uses the rule's return value.
    # Actually, the rule itself returns the confidence.

    # Let's add a custom high-confidence exclusion rule

    class HighConfidenceExclusion(ExclusionPatternRule):
        def evaluate(self, response_text: str, platform: str, username: str) -> tuple[ValidationVote, float]:
            return ValidationVote.INVALID, 0.99

    validator.add_rule(HighConfidenceExclusion(name="HighConfidenceExclusion"))

    response_text = "User not found"
    platform = "generic"

    # This should now be invalid because of high confidence exclusion
    result = validator.validate_with_details(response_text, platform)

    assert result.is_valid is False
