from unittest.mock import MagicMock

from osint_nexus.core.platform_fingerprinter import PlatformFingerprinter


def test_platform_fingerprinter() -> None:
    ml_model = MagicMock()
    ml_model.predict_pattern.return_value = ["new_pattern"]

    fingerprinter = PlatformFingerprinter(
        twitter_token="fake_twitter", github_token="fake_github", ml_model=ml_model
    )

    # Test fingerprint structure
    assert "twitter" in fingerprinter.fingerprints
    assert "github" in fingerprinter.fingerprints
    twitter_fingerprint = fingerprinter.fingerprints["twitter"]
    assert isinstance(twitter_fingerprint, dict)
    assert twitter_fingerprint["headers"]["Authorization"] == "Bearer fake_twitter"

    # Test pattern detection
    patterns = fingerprinter.detect_platform_patterns("testuser")
    assert patterns == []  # Since auto_discover_platforms returns []

    ml_model.predict_pattern.assert_called_with("testuser")
