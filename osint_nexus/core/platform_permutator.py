from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger("osint_nexus.platform_permutator")


@runtime_checkable
class PlatformVariationStrategy(Protocol):
    """Protocol for generating platform variations (e.g., TLD, subdomain)."""

    def apply(self, platform: str) -> set[str]: ...


class TLDVariationStrategy:
    """Generates variations like .com, .org, .io."""

    def apply(self, platform: str) -> set[str]:
        # Implementation placeholder
        return {f"{platform.split('.')[0]}.com", f"{platform.split('.')[0]}.org"}


class SubdomainVariationStrategy:
    """Generates variations like app., api., mobile."""

    def apply(self, platform: str) -> set[str]:
        return {f"app.{platform}", f"api.{platform}", f"mobile.{platform}"}


class CountryVariationStrategy:
    """Generates variations like .uk, .de, .fr."""

    def apply(self, platform: str) -> set[str]:
        base = platform.split(".")[0]
        return {f"{base}.uk", f"{base}.de", f"{base}.fr"}


class MobileVariationStrategy:
    """Generates variations like m., mobile."""

    def apply(self, platform: str) -> set[str]:
        return {f"m.{platform}", f"mobile.{platform}"}


class APIVariationStrategy:
    """Generates variations like api."""

    def apply(self, platform: str) -> set[str]:
        return {f"api.{platform}"}


class GraphQLVariationStrategy:
    """Generates variations like graphql."""

    def apply(self, platform: str) -> set[str]:
        return {f"graphql.{platform}"}


class LegacyVariationStrategy:
    """Generates variations like old., v1."""

    def apply(self, platform: str) -> set[str]:
        return {f"old.{platform}", f"v1.{platform}"}


class CDNVariationStrategy:
    """Generates variations like cdn., static."""

    def apply(self, platform: str) -> set[str]:
        return {f"cdn.{platform}", f"static.{platform}"}


class PlatformPermutator:
    """
    Advanced generator for target platform variations.
    """

    def __init__(self, strategies: list[PlatformVariationStrategy] | None = None) -> None:
        self._strategies = strategies or [
            TLDVariationStrategy(),
            SubdomainVariationStrategy(),
            CountryVariationStrategy(),
            MobileVariationStrategy(),
            APIVariationStrategy(),
            GraphQLVariationStrategy(),
            LegacyVariationStrategy(),
            CDNVariationStrategy(),
        ]
        self._logger = logging.getLogger(f"osint_nexus.permutator.{self.__class__.__name__}")

    def generate(self, platforms: list[str]) -> set[str]:
        variations = set()
        for platform in platforms:
            for strategy in self._strategies:
                variations.update(strategy.apply(platform))
        return variations
