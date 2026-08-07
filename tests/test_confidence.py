import pytest

from osint_nexus.core.confidence import ConfidenceEngine
from osint_nexus.core.models import Factor


def test_confidence_basic() -> None:
    """Test basic confidence score calculation with default platform weights."""
    engine = ConfidenceEngine()

    # LinkedIn (12.0) + GitHub (10.0) = 22.0
    # Target weight for max is 30.0 -> base score = (22 / 30) * 100 = 73.33%
    result = engine.calculate_confidence(["linkedin", "github"])

    assert pytest.approx(result.score, 0.1) == 73.3
    assert result.category == "Medium"  # 60 <= score < 85 is Medium


def test_confidence_with_multipliers_and_bonuses() -> None:
    """Test confidence with multipliers and bonuses."""
    engine = ConfidenceEngine()

    # LinkedIn (12.0) + GitHub (10.0) = 22.0 -> base score = 73.33%
    # Multiplier: dormant (0.8) -> 58.66%
    # Bonus: device_match (+25.0) -> 83.66%
    result = engine.calculate_confidence(
        ["linkedin", "github"], multipliers={"dormant": 0.8}, additive_bonuses={"device_match": 25.0}
    )

    assert pytest.approx(result.score, 0.1) == 83.6
    assert result.category == "Medium"  # 60 <= score < 85 is Medium


def test_confidence_invalid_multiplier() -> None:
    """Test that invalid multipliers raise ValueError."""
    engine = ConfidenceEngine()

    # Multiplier > 1.0 should now raise ValueError due to strict Factor validation
    with pytest.raises(ValueError, match="Multiplier 'invalid' must be between 0.0 and 1.0"):
        engine.calculate_confidence(["linkedin"], multipliers={"invalid": 1.5})


def test_confidence_over_100() -> None:
    """Test that multipliers are applied correctly even when base score > 100%."""
    engine = ConfidenceEngine()
    # High base score > 100
    engine.set_target_weight(10.0)  # Base 100 is now 10.0 total weight
    # LinkedIn (12.0) = 120% base score
    # Multiplier: dormant (0.5) -> Should be 60.0%
    result = engine.calculate_confidence(["linkedin"], multipliers={"dormant": 0.5})
    assert result.score == 60.0


def test_set_platform_weight() -> None:
    engine = ConfidenceEngine()
    engine.set_platform_weight("new_platform", 20.0)
    assert engine.get_platform_weight("new_platform") == 20.0

    with pytest.raises(ValueError, match="Platform weight must be non‑negative"):
        engine.set_platform_weight("new_platform", -5.0)


def test_create_factors() -> None:
    engine = ConfidenceEngine()
    # Test valid
    factors = engine._create_factors({"m1": 0.5}, {"b1": 10.0})
    assert len(factors) == 2

    # Test invalid factor type
    with pytest.raises(ValueError, match="Factor type must be either 'multiplier' or 'bonus'"):
        # This is tricky as _create_factors enforces type in Factor init.
        # But we can test Factor directly.
        Factor("invalid", 0.5, "wrong_type")


def test_apply_factors() -> None:
    engine = ConfidenceEngine()

    factors = [Factor("m1", 0.5, "multiplier"), Factor("b1", 10.0, "bonus")]
    detail: dict[str, float] = {}
    # Base 100 -> (100 * 0.5) + 10.0 = 60.0
    score = engine._apply_factors(100.0, factors, detail)
    assert score == 60.0
    assert detail["multiplier_m1"] == 0.5
    assert detail["bonus_b1"] == 10.0
