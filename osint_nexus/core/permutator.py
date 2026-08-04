from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol

logger = logging.getLogger("osint_nexus.permutator")


@dataclass(frozen=True, slots=True)
class PermutationConfig:
    """
    Configuration profile for username generation.
    Immutable to ensure thread-safety across async workflows.
    """

    min_length: int = 3
    max_length: int = 30
    separators: tuple[str, ...] = (".", "-", "_")
    common_suffixes: tuple[str, ...] = ("123", "official", "real", "bot", "_")
    common_prefixes: tuple[str, ...] = ("the", "real", "its", "official")
    use_leetspeak: bool = False

    # Mapping for basic character substitution (vowels to numbers)
    leet_map: dict[int, int] = field(
        default_factory=lambda: str.maketrans("aeioAEIO", "43104310"), repr=False
    )


class PermutationStrategy(Protocol):
    """Protocol for username generation strategies."""

    def apply(self, base: str, original: str, parts: list[str], config: PermutationConfig) -> set[str]: ...


class AffixStrategy:
    """Generates variants with common OSINT prefixes and suffixes."""

    def apply(self, base: str, original: str, parts: list[str], config: PermutationConfig) -> set[str]:
        affixed = set()
        # Suffixes
        for suffix in config.common_suffixes:
            affixed.add(f"{base}{suffix}")
            if original != base:
                affixed.add(f"{original}{suffix}")
        # Prefixes
        for prefix in config.common_prefixes:
            affixed.add(f"{prefix}{base}")
            affixed.add(f"{prefix}_{base}")
        return affixed


class LeetSpeakStrategy:
    """Translates variants into leetspeak format."""

    def apply(self, base: str, original: str, parts: list[str], config: PermutationConfig) -> set[str]:
        return {base.translate(config.leet_map)}


class SeparatorStrategy:
    """Generates variants by rotating separators between parts."""

    def apply(self, base: str, original: str, parts: list[str], config: PermutationConfig) -> set[str]:
        variants = set()
        if len(parts) > 1:
            for sep in config.separators:
                variants.add(sep.join(parts))
        return variants


class UsernamePermutator:
    """
    Advanced generator for target username permutations.
    Orchestrates multiple permutation strategies.
    """

    def __init__(self, config: PermutationConfig | None = None) -> None:
        self.config = config or PermutationConfig()
        self._logger = logging.getLogger(f"osint_nexus.permutator.{self.__class__.__name__}")
        self._separator_re = re.compile(r"[\._-]")
        self._strategies: list[PermutationStrategy] = [
            SeparatorStrategy(),
            AffixStrategy(),
        ]
        if self.config.use_leetspeak:
            self._strategies.append(LeetSpeakStrategy())

    def generate(self, username: str) -> set[str]:
        if not username or not username.strip():
            return set()

        username = username.lower().strip()
        parts = [p for p in self._separator_re.split(username) if p]

        if not parts:
            return set()

        clean_base = "".join(parts)
        raw_permutations: set[str] = {username, clean_base}

        # Apply strategies
        for strategy in self._strategies:
            # Basic length guard to prevent explosion
            if len(clean_base) < (self.config.max_length - 8):
                raw_permutations.update(strategy.apply(clean_base, username, parts, self.config))

        return self._filter_valid(raw_permutations)

    def _filter_valid(self, variants: Iterable[str]) -> set[str]:
        valid_set = set()
        for variant in variants:
            if self.config.min_length <= len(variant) <= self.config.max_length and not variant.startswith(
                self.config.separators
            ):
                valid_set.add(variant)

        return valid_set
