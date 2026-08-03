"""
Pivot Extractor for secondary identifier harvesting.

Automatically harvests secondary identifiers like bio text, external links,
and public emails from validated profile pages.
"""

from __future__ import annotations

import logging
import re
import typing
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger("osint_nexus.core.extractor")


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


class LinkSocialExtractor:
    def __init__(self) -> None:
        self.social_domains = {
            "twitter.com": "Twitter",
            "x.com": "Twitter",
            "instagram.com": "Instagram",
            "linkedin.com": "LinkedIn",
            "github.com": "GitHub",
            "facebook.com": "Facebook",
            "youtube.com": "YouTube",
        }

    def extract(self, soup: BeautifulSoup, source_url: str | None = None) -> dict[str, list[Any]]:
        external_links: set[str] = set()
        social_handles: list[dict[str, str]] = []
        source_domain = urlparse(source_url).netloc.lower() if source_url else ""

        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if not isinstance(href, str) or not href.startswith(("http://", "https://")):
                continue

            parsed_href = urlparse(href)
            href_domain = parsed_href.netloc.lower()

            if source_domain and (href_domain == source_domain or href_domain.endswith("." + source_domain)):
                continue

            external_links.add(href)

            # Check social
            for dom, platform in self.social_domains.items():
                if href_domain == dom or href_domain.endswith("." + dom):
                    path_parts = [p for p in parsed_href.path.split("/") if p]
                    if path_parts and path_parts[0] not in ("share", "home", "intent", "search", "p"):
                        social_handles.append({"platform": platform, "username": path_parts[0], "url": href})
                        break

        return {"external_links": list(external_links), "social_handles": social_handles}


class BioExtractor:
    def extract(self, soup: BeautifulSoup) -> str:
        # Meta tags
        for attr in ["description", "og:description", "twitter:description"]:
            meta = soup.find("meta", attrs={"name": attr} if "description" in attr else {"property": attr})
            if meta and meta.get("content"):
                return str(meta["content"]).strip()

        # Elements
        for selector in [
            {"class": re.compile(r"bio|profile-bio|user-bio|about|description|summary", re.I)},
            {"id": re.compile(r"bio|about|description|summary", re.I)},
        ]:
            element = soup.find(name=None, attrs=typing.cast(typing.Any, selector))
            if element:
                text = element.get_text(strip=True)
                if len(text) > 5:
                    return text
        return "Bio extraction not fully implemented."


class PivotExtractor:
    """
    Parses HTML content using BeautifulSoup and regex to extract secondary identifiers.
    """

    def __init__(self) -> None:
        self.email_extractor = EmailExtractor()
        self.pgp_extractor = PgpExtractor()
        self.link_social_extractor = LinkSocialExtractor()
        self.bio_extractor = BioExtractor()

    async def extract(self, content: str, source_url: str | None = None) -> dict[str, Any]:
        """
        Parses the content and returns a dictionary of harvested identifiers.
        """
        soup = BeautifulSoup(content, "html.parser")

        emails = self.email_extractor.extract(content, soup)
        pgp_keys = self.pgp_extractor.extract(content)
        links_info = self.link_social_extractor.extract(soup, source_url)
        bio = self.bio_extractor.extract(soup)

        extracted = {
            "emails": emails,
            "pgp_keys": pgp_keys,
            "external_links": links_info["external_links"],
            "social_handles": links_info["social_handles"],
            "bio": bio,
        }
        logger.debug("Extracted pivots: %s", extracted)
        return dict(extracted)
