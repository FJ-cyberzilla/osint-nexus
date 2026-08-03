"""
Pivot Extractor for secondary identifier harvesting.

Automatically harvests secondary identifiers like bio text, external links,
and public emails from validated profile pages.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger("osint_nexus.core.extractor")


class PivotExtractor:
    """
    Parses HTML content using BeautifulSoup and regex to extract secondary identifiers.
    """

    def __init__(self) -> None:
        self.email_pattern = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self.pgp_pattern = re.compile(
            r"-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----"
        )
        # Social domains to detect connected handles
        self.social_domains = {
            "twitter.com": "Twitter",
            "x.com": "Twitter",
            "instagram.com": "Instagram",
            "linkedin.com": "LinkedIn",
            "github.com": "GitHub",
            "facebook.com": "Facebook",
            "youtube.com": "YouTube",
        }

    async def extract(self, content: str, source_url: str | None = None) -> dict[str, Any]:
        """
        Parses the content and returns a dictionary of harvested identifiers.
        """
        soup = BeautifulSoup(content, "html.parser")

        emails = self._extract_emails(content, soup)
        pgp_keys = self._extract_pgp_keys(content)
        links_info = self._extract_links_and_socials(soup, source_url)
        bio = self._extract_bio(soup)

        extracted = {
            "emails": emails,
            "pgp_keys": pgp_keys,
            "external_links": links_info["external_links"],
            "social_handles": links_info["social_handles"],
            "bio": bio,
        }
        logger.debug("Extracted pivots: %s", extracted)
        return dict(extracted)

    def _extract_emails(self, content: str, soup: BeautifulSoup) -> list[str]:
        """Extract emails from text and mailto links."""
        emails = set(self.email_pattern.findall(content))
        for a in soup.find_all("a", href=True):
            href_attr = a.get("href")
            if not isinstance(href_attr, str):
                continue

            if href_attr.startswith("mailto:"):
                email = href_attr.replace("mailto:", "").split("?")[0].strip()
                if self.email_pattern.match(email):
                    emails.add(email)
        return list(emails)

    def _extract_pgp_keys(self, content: str) -> list[str]:
        """Extract PGP public key blocks."""
        return [block.strip() for block in self.pgp_pattern.findall(content)]

    def _extract_links_and_socials(
        self, soup: BeautifulSoup, source_url: str | None = None
    ) -> dict[str, list[Any]]:
        """Extract external links and identify potential connected social handles."""
        external_links: set[str] = set()
        social_handles: list[dict[str, str]] = []
        source_domain = self._get_source_domain(source_url)

        for a in soup.find_all("a", href=True):
            self._process_link(a, source_domain, external_links, social_handles)

        return {"external_links": list(external_links), "social_handles": social_handles}
        
    def _process_link(self, a: Any, source_domain: str, external_links: set[str], social_handles: list[dict[str, str]]) -> None:
        href = a.get("href")
        if not self._is_external_http_url(href):
            return

        parsed_href = urlparse(href)
        if self._is_internal_domain(parsed_href.netloc.lower(), source_domain):
            return

        external_links.add(href)
        self._add_social_handle_if_found(parsed_href, href, social_handles)

    def _is_external_http_url(self, href: Any) -> bool:
        return isinstance(href, str) and href.startswith(("http://", "https://"))

    def _is_internal_domain(self, href_domain: str, source_domain: str) -> bool:
        if not source_domain:
            return False
        # Matches if it's the exact same domain, or a subdomain.
        # This prevents prefix attacks like "not-example.com".
        return href_domain == source_domain or href_domain.endswith("." + source_domain)

    def _add_social_handle_if_found(self, parsed_href: Any, href: str, social_handles: list[dict[str, str]]) -> None:
        handle = self._get_social_handle(parsed_href, href)
        if handle:
            social_handles.append(handle)

    def _get_source_domain(self, source_url: str | None) -> str:
        if not source_url:
            return ""
        return urlparse(source_url).netloc.lower()
        
    def _get_social_handle(self, parsed_href: Any, href: str) -> dict[str, str] | None:
        href_domain = parsed_href.netloc.lower()
        for dom, platform in self.social_domains.items():
            # Check for exact match or subdomain.
            # This prevents prefix attacks like "not-twitter.com".
            if href_domain == dom or href_domain.endswith("." + dom):
                return self._parse_username(platform, href, parsed_href.path)
        return None
        
    def _parse_username(self, platform: str, href: str, path: str) -> dict[str, str] | None:
        path_parts = [p for p in path.split("/") if p]
        if not path_parts:
            return None
        username = path_parts[0]
        if username in ("share", "home", "intent", "search", "p"):
            return None
        return {"platform": platform, "username": username, "url": href}

    def _extract_bio(self, soup: BeautifulSoup) -> str:
        """Heuristic-based bio extraction."""
        
        bio = self._get_meta_bio(soup)
        if bio:
            return bio

        bio = self._get_element_bio(soup)
        if bio:
            return bio

        return "Bio extraction not fully implemented."
        
    def _get_meta_bio(self, soup: BeautifulSoup) -> str | None:
        """Extract bio from meta tags."""
        meta_desc = (
            soup.find("meta", attrs={"name": "description"})
            or soup.find("meta", attrs={"property": "og:description"})
            or soup.find("meta", attrs={"name": "twitter:description"})
        )
        if meta_desc and meta_desc.get("content"):
            return str(meta_desc["content"]).strip()
        return None
        
    def _get_element_bio(self, soup: BeautifulSoup) -> str | None:
        # 2. Look for elements with common "bio" or "about" class/id
        # Define attributes explicitly as dict[str, Any]
        bio_selectors: list[dict[str, Any]] = [
            {"class": re.compile(r"bio|profile-bio|user-bio|about|description|summary", re.I)},
            {"id": re.compile(r"bio|about|description|summary", re.I)},
        ]
        for selector in bio_selectors:
            # Pass the selector dict directly. BeautifulSoup should handle this if it's not ambiguous.
            # If still ambiguous, specify the name parameter as None.
            element = soup.find(name=None, attrs=selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 5:  # Avoid trivial matches
                    return text
        return None
