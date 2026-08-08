from osint_nexus.core.compliance import ComplianceEngine, Scrubbable


def test_compliance_redaction() -> None:
    engine = ComplianceEngine()
    data: dict[str, Scrubbable] = {
        "user": "johndoe",
        "email": "john@example.com",
        "profile": {"bio": "Contact me at 555-123-4567 or john.doe@work.com"},
        "tags": ["admin", "555-987-6543"],
    }

    sanitized = engine.sanitize(data)

    assert sanitized["email"] == "[REDACTED]"

    profile = sanitized["profile"]
    assert isinstance(profile, dict)
    bio = profile["bio"]
    assert isinstance(bio, str)
    assert "[REDACTED]" in bio

    tags = sanitized["tags"]
    assert isinstance(tags, list)
    assert "[REDACTED]" in tags

    assert sanitized["user"] == "johndoe"


def test_compliance_no_pii() -> None:
    engine = ComplianceEngine()
    data: dict[str, Scrubbable] = {"user": "johndoe", "bio": "Just a normal person"}
    sanitized = engine.sanitize(data)
    assert sanitized == data
