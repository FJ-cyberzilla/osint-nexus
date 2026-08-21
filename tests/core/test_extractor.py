import pytest
from bs4 import BeautifulSoup

from osint_nexus.core.extractor import LinkSocialExtractor, extract_ioc
from osint_nexus.core.type_defs import IOCType, ExtractedIOC, SocialHandle


def test_is_internal_domain_security() -> None:
    extractor = LinkSocialExtractor()
    source_url = "http://example.com"

    def _test(href: str, should_be_internal: bool) -> None:
        html = f'<a href="{href}">link</a>'
        soup = BeautifulSoup(html, "html.parser")
        result = extractor.extract(soup, source_url)
        # If internal, it shouldn't be in external_links
        is_internal = href not in result["external_links"]
        assert is_internal == should_be_internal

    _test("http://example.com", True)
    _test("http://sub.example.com", True)
    _test("http://not-example.com", False)
    _test("http://example.com.evil.com", False)


def test_get_social_handle_security() -> None:
    extractor = LinkSocialExtractor()

    def _get_social(url: str) -> SocialHandle | None:
        html = f'<a href="{url}">link</a>'
        soup = BeautifulSoup(html, "html.parser")
        result = extractor.extract(soup)
        handles = result["social_handles"]
        return handles[0] if handles else None

    # Positive case
    result = _get_social("https://twitter.com/user")
    assert result is not None
    assert result["platform"] == "Twitter"

    # Subdomain case
    result = _get_social("https://sub.twitter.com/user")
    assert result is not None
    assert result["platform"] == "Twitter"

    # Negative case (vulnerability fix check)
    result = _get_social("https://not-twitter.com/user")
    assert result is None


def test_extract_ioc_all_types() -> None:
    # Test IPv4
    content_ip = "Connecting to 192.168.1.1 and 10.0.0.254 for analysis."
    ips = extract_ioc(content_ip, IOCType.IPV4)
    assert len(ips) == 2
    assert ips[0] == ExtractedIOC(type=IOCType.IPV4, value="192.168.1.1")
    assert ips[1] == ExtractedIOC(type=IOCType.IPV4, value="10.0.0.254")

    # Test Domain
    content_domain = "Visit our sites: safety.osint-nexus.local and detect.net now."
    domains = extract_ioc(content_domain, IOCType.DOMAIN)
    assert len(domains) == 2
    assert domains[0] == ExtractedIOC(type=IOCType.DOMAIN, value="safety.osint-nexus.local")
    assert domains[1] == ExtractedIOC(type=IOCType.DOMAIN, value="detect.net")

    # Test SHA256
    content_sha256 = "File hash is e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855."
    shas = extract_ioc(content_sha256, IOCType.SHA256)
    assert len(shas) == 1
    assert shas[0] == ExtractedIOC(type=IOCType.SHA256, value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    # Test MD5
    content_md5 = "Secondary hash is 098f6bcd4621d373cade4e832627b4f6 in registry."
    md5s = extract_ioc(content_md5, IOCType.MD5)
    assert len(md5s) == 1
    assert md5s[0] == ExtractedIOC(type=IOCType.MD5, value="098f6bcd4621d373cade4e832627b4f6")

    # Test Email
    content_email = "Reach out via threat-team@osint-nexus.org or admin@security.com."
    emails = extract_ioc(content_email, IOCType.EMAIL)
    assert len(emails) == 2
    assert emails[0] == ExtractedIOC(type=IOCType.EMAIL, value="threat-team@osint-nexus.org")
    assert emails[1] == ExtractedIOC(type=IOCType.EMAIL, value="admin@security.com")


from beartype.roar import BeartypeCallHintParamViolation

def test_extract_ioc_beartype_runtime_safety() -> None:
    # Verify parameter type validation at the runtime boundary
    with pytest.raises(BeartypeCallHintParamViolation):
        # Passing an invalid type (integer) for content
        extract_ioc(12345, IOCType.EMAIL)  # type: ignore[arg-type]

    with pytest.raises(BeartypeCallHintParamViolation):
        # Passing an invalid type (string) for ioc_type
        extract_ioc("some content", "invalid_type")  # type: ignore[arg-type]

