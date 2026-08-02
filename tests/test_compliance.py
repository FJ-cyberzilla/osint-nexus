from osint_nexus.core.compliance import ComplianceEngine


def test_compliance_redaction() -> None:
    engine = ComplianceEngine()
    data = {
        "user": "johndoe",
        "email": "john@example.com",
        "profile": {"bio": "Contact me at 555-123-4567 or john.doe@work.com"},
        "tags": ["admin", "555-987-6543"],
    }

    sanitized = engine.sanitize(data)

    assert sanitized["email"] == "[REDACTED]"
    assert "[REDACTED]" in sanitized["profile"]["bio"]
    assert "[REDACTED]" in sanitized["tags"]
    assert sanitized["user"] == "johndoe"


def test_compliance_no_pii() -> None:
    engine = ComplianceEngine()
    data = {"user": "johndoe", "bio": "Just a normal person"}
    sanitized = engine.sanitize(data)
    assert sanitized == data
