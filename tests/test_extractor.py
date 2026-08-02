import pytest
from unittest.mock import MagicMock
from osint_nexus.core.extractor import PivotExtractor

def test_is_internal_domain_security():
    extractor = PivotExtractor()
    source_domain = "example.com"
    
    # Positive cases
    assert extractor._is_internal_domain("example.com", source_domain) is True
    assert extractor._is_internal_domain("sub.example.com", source_domain) is True
    
    # Negative cases (vulnerability fix check)
    assert extractor._is_internal_domain("not-example.com", source_domain) is False
    assert extractor._is_internal_domain("example.com.evil.com", source_domain) is False

def test_get_social_handle_security():
    extractor = PivotExtractor()
    
    # Mocking parsed_href
    parsed_href = MagicMock()
    
    # Positive case
    parsed_href.netloc = "twitter.com"
    parsed_href.path = "/user"
    result = extractor._get_social_handle(parsed_href, "https://twitter.com/user")
    assert result is not None
    assert result["platform"] == "Twitter"
    
    # Subdomain case
    parsed_href.netloc = "sub.twitter.com"
    parsed_href.path = "/user"
    result = extractor._get_social_handle(parsed_href, "https://sub.twitter.com/user")
    assert result is not None
    assert result["platform"] == "Twitter"

    # Negative case (vulnerability fix check)
    parsed_href.netloc = "not-twitter.com"
    parsed_href.path = "/user"
    result = extractor._get_social_handle(parsed_href, "https://not-twitter.com/user")
    assert result is None
