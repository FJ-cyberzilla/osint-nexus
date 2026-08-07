"""
Pivot Extractor for secondary identifier harvesting.

Automatically harvests secondary identifiers like bio text, external links,
and public emails from validated profile pages.
"""

from __future__ import annotations

import logging
import re
from typing import Protocol, TypedDict
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger("osint_nexus.core.extractor")

# Define a specific type for extracted pivots
type ExtractedPivots = dict[str, list[str] | list[dict[str, str]] | str | None]


class EmailExtractor:
    def __init__(self) -> None:
        self.email_pattern = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

    def extract(self, content: str, soup: BeautifulSoup) -> list[str]:
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


class PgpExtractor:
    def __init__(self) -> None:
        self.pgp_pattern = re.compile(
            r"-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----"
        )

    def extract(self, content: str) -> list[str]:
        return [block.strip() for block in self.pgp_pattern.findall(content)]


class SocialPlatformRegistry:
    """Registry for social platform identification and username extraction."""

    PLATFORMS = {
        "twitter.com": "Twitter",
        "x.com": "Twitter",
        "instagram.com": "Instagram",
        "linkedin.com": "LinkedIn",
        "github.com": "GitHub",
        "facebook.com": "Facebook",
        "youtube.com": "YouTube",
    }
    IGNORED_PATHS = {"share", "home", "intent", "search", "p"}

    def identify(self, domain: str, path: str) -> dict[str, str] | None:
        platform = self._get_platform(domain)
        if not platform:
            return None

        username = self._extract_username(path)
        if not username:
            return None

        return {"platform": platform, "username": username}

    def _get_platform(self, domain: str) -> str | None:
        for dom, name in self.PLATFORMS.items():
            if domain == dom or domain.endswith("." + dom):
                return name
        return None

    def _extract_username(self, path: str) -> str | None:
        path_parts = [p for p in path.split("/") if p]
        if path_parts and path_parts[0] not in self.IGNORED_PATHS:
            return path_parts[0]
        return None


class LinkHarvester:
    """Harvests external links from a page, excluding the source domain."""

    def harvest(self, soup: BeautifulSoup, source_url: str | None = None) -> set[str]:
        """Harvests all valid external links from the soup."""
        source_domain = urlparse(source_url).netloc.lower() if source_url else ""

        # Extract and filter hrefs using comprehension for better performance and readability
        links = {
            href
            for a in soup.find_all("a", href=True)
            if isinstance((href := a.get("href")), str) and self._is_valid_link(href, source_domain)
        }

        return links

    def _is_valid_link(self, link: str, source_domain: str) -> bool:
        """Validates if a link is an external http/https URL."""
        return link.startswith(("http://", "https://")) and self._is_external(link, source_domain)

    def _is_external(self, href: str, source_domain: str) -> bool:
        """Checks if the link belongs to a different domain."""
        href_domain = urlparse(href).netloc.lower()
        if not source_domain:
            return True
        return not (href_domain == source_domain or href_domain.endswith("." + source_domain))


class SocialIdentityExtractor:
    """Extracts social handles from harvested links."""

    def __init__(self, registry: SocialPlatformRegistry) -> None:
        self.registry = registry

    def extract(self, links: set[str]) -> list[dict[str, str]]:
        social_handles = []
        for link in links:
            parsed = urlparse(link)
            identity = self.registry.identify(parsed.netloc.lower(), parsed.path)
            if identity:
                identity["url"] = link
                social_handles.append(identity)
        return social_handles


class LinkHarvestResult(TypedDict):
    external_links: list[str]
    social_handles: list[dict[str, str]]


class LinkSocialExtractor:
    """Orchestrates link harvesting and social identity extraction."""

    def __init__(self) -> None:
        self.harvester = LinkHarvester()
        self.registry = SocialPlatformRegistry()
        self.social_extractor = SocialIdentityExtractor(self.registry)

    def extract(self, soup: BeautifulSoup, source_url: str | None = None) -> LinkHarvestResult:
        links = self.harvester.harvest(soup, source_url)
        social_handles = self.social_extractor.extract(links)
        return {"external_links": list(links), "social_handles": social_handles}


class BioExtractionStrategy(Protocol):
    def extract(self, soup: BeautifulSoup) -> str | None: ...


class MetaTagBioStrategy:
    def __init__(self) -> None:
        self.targets = [
            ("name", "description"),
            ("property", "og:description"),
            ("property", "twitter:description"),
        ]

    def extract(self, soup: BeautifulSoup) -> str | None:
        for attr, value in self.targets:
            # Use find with attrs dict for robust searching
            meta = soup.find("meta", attrs={attr: value})
            # meta.get("content") returns Optional[Any], explicitly check and cast to str
            content = meta.get("content") if meta else None
            if isinstance(content, str):
                return content.strip()
        return None


class HeuristicElementBioStrategy:
    def __init__(self) -> None:
        self.selectors: list[dict[str, re.Pattern[str]]] = [
            {"class": re.compile(r"bio|profile-bio|user-bio|about|description|summary", re.I)},
            {"id": re.compile(r"bio|about|description|summary", re.I)},
        ]

    def extract(self, soup: BeautifulSoup) -> str | None:
        for selector in self.selectors:
            element = soup.find(name=None, attrs=selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 5:
                    return text
        return None


class BioExtractor:
    """Orchestrates bio extraction using multiple strategies."""

    def __init__(self) -> None:
        self.strategies: list[BioExtractionStrategy] = [
            MetaTagBioStrategy(),
            HeuristicElementBioStrategy(),
        ]

    def extract(self, soup: BeautifulSoup) -> str:
        for strategy in self.strategies:
            bio = strategy.extract(soup)
            if bio:
                return bio
        return "Bio extraction not fully implemented."


class PivotExtractor:
    """
    Parses HTML content using BeautifulSoup and regex to extract secondary identifiers.
    """

    def __init__(self) -> None:
        """Initializes the PivotExtractor with all sub-extractors."""
        self.email_extractor = EmailExtractor()
        self.pgp_extractor = PgpExtractor()
        self.link_social_extractor = LinkSocialExtractor()
        self.bio_extractor = BioExtractor()

    async def extract(self, content: str, source_url: str | None = None) -> ExtractedPivots:
        """
        Parses the content and returns a dictionary of harvested identifiers.

        Args:
            content: The raw HTML content to parse.
            source_url: Optional source URL of the content.

        Returns:
            A dictionary containing harvested emails, PGP keys, links, handles, and bio.
        """
        soup = BeautifulSoup(content, "html.parser")

        emails = self.email_extractor.extract(content, soup)
        pgp_keys = self.pgp_extractor.extract(content)
        links_info = self.link_social_extractor.extract(soup, source_url)
        bio = self.bio_extractor.extract(soup)

        extracted: ExtractedPivots = {
            "emails": emails,
            "pgp_keys": pgp_keys,
            "external_links": links_info["external_links"],
            "social_handles": links_info["social_handles"],
            "bio": bio,
        }
        logger.debug("Extracted pivots: %s", extracted)
        return extracted
