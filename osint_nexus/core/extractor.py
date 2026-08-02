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
        external_links = set()
        social_handles = []

        source_domain = ""
        if source_url:
            parsed_source = urlparse(source_url)
            source_domain = parsed_source.netloc.lower()

        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if not isinstance(href, str):
                continue

            if href.startswith(("http://", "https://")):
                parsed_href = urlparse(href)
                href_domain = parsed_href.netloc.lower()

                # Filter out current platform domain
                if source_domain and source_domain in href_domain:
                    continue

                external_links.add(href)

                # Check for social handles
                for dom, platform in self.social_domains.items():
                    if dom in href_domain:
                        # Extract the path (e.g. /username)
                        path_parts = [p for p in parsed_href.path.split("/") if p]
                        if path_parts:
                            username = path_parts[0]
                            # Avoid common non-username paths
                            if username not in ("share", "home", "intent", "search", "p"):
                                social_handles.append(
                                    {"platform": platform, "username": username, "url": href}
                                )

        return {"external_links": list(external_links), "social_handles": social_handles}

    def _extract_bio(self, soup: BeautifulSoup) -> str:
        """Heuristic-based bio extraction."""
        # 1. Try common meta description tags
        meta_desc = (
            soup.find("meta", attrs={"name": "description"})
            or soup.find("meta", attrs={"property": "og:description"})
            or soup.find("meta", attrs={"name": "twitter:description"})
        )
        if meta_desc and meta_desc.get("content"):
            return str(meta_desc["content"]).strip()

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

        return "Bio extraction not fully implemented."
