from bs4 import BeautifulSoup

from osint_nexus.core.extractor import LinkSocialExtractor


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

    def _get_social(url: str) -> dict[str, str] | None:
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
