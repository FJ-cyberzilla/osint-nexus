"""
Username permutation engine for OSINT Nexus.

Generates smart, highly probable variations of target handles to maximize 
platform scan coverage. Designed to be stateless, thread-safe, and 
configurable for concurrent pipeline execution.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field

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
        default_factory=lambda: str.maketrans("aeioAEIO", "43104310"),
        repr=False
    )


class UsernamePermutator:
    """
    Advanced generator for target username permutations.
    
    Extracts the semantic base of a handle and applies combinatorial rules
    (separators, affixes, leetspeak) to yield highly probable variants,
    while discarding invalid or redundant outputs.
    """

    def __init__(self, config: PermutationConfig | None = None) -> None:
        """
        Initialize the permutator with an optional configuration profile.
        """
        self.config = config or PermutationConfig()
        self._logger = logging.getLogger(f"osint_nexus.permutator.{self.__class__.__name__}")
        
        # Pre-compile regex for performance in high-throughput loops
        self._separator_re = re.compile(r"[\._-]")

    def generate(self, username: str) -> set[str]:
        """
        Generate a strictly filtered set of username permutations.

        Args:
            username: The baseline target handle.

        Returns:
            A deduplicated set of valid username variations.
        """
        if not username or not username.strip():
            self._logger.debug("Received empty username; returning empty set.")
            return set()

        username = username.lower().strip()
        raw_permutations: set[str] = {username}

        # 1. Semantic Extraction (handle multiple adjacent separators safely)
        parts = [p for p in self._separator_re.split(username) if p]
        
        if not parts:
            # Edge case: Username was entirely comprised of separators (e.g., "___")
            return self._filter_valid(raw_permutations)

        clean_base = "".join(parts)
        raw_permutations.add(clean_base)

        # 2. Separator Rotation
        if len(parts) > 1:
            for sep in self.config.separators:
                raw_permutations.add(sep.join(parts))

        # 3. Smart Affixing (Prefixes & Suffixes)
        # We only affix if the base isn't already excessively long, avoiding bloat.
        if len(clean_base) < (self.config.max_length - 8):
            raw_permutations.update(self._generate_affixes(clean_base, username))

        # 4. Leetspeak Injection
        if self.config.use_leetspeak:
            raw_permutations.update(self._generate_leetspeak(raw_permutations))

        # 5. Validation & Filtering
        valid_permutations = self._filter_valid(raw_permutations)
        
        self._logger.debug(
            "Generated %d valid permutations for base target '%s'.", 
            len(valid_permutations), 
            username
        )
        
        return valid_permutations

    def _generate_affixes(self, clean_base: str, original_username: str) -> set[str]:
        """Generates variants with common OSINT prefixes and suffixes."""
        affixed = set()
        
        # Suffixes
        for suffix in self.config.common_suffixes:
            affixed.add(f"{clean_base}{suffix}")
            # Only add to the original if it actually differs from clean_base
            if original_username != clean_base:
                affixed.add(f"{original_username}{suffix}")
                
        # Prefixes
        for prefix in self.config.common_prefixes:
            affixed.add(f"{prefix}{clean_base}")
            affixed.add(f"{prefix}_{clean_base}")
            
        return affixed

    def _generate_leetspeak(self, current_variants: set[str]) -> set[str]:
        """Translates existing variants into leetspeak format."""
        # We translate the variants rather than purely appending to prevent exponential explosion
        return {variant.translate(self.config.leet_map) for variant in current_variants}

    def _filter_valid(self, variants: Iterable[str]) -> set[str]:
        """
        Enforces platform constraints to prevent unnecessary network requests.
        """
        valid_set = set()
        for variant in variants:
            # Rule 1: Length bounds
            if self.config.min_length <= len(variant) <= self.config.max_length:
                # Rule 2: Cannot start or end with a separator (violates most platform rules)
                if not variant.startswith(self.config.separators) and not variant.endswith(self.config.separators):
                    valid_set.add(variant)
                    
        return valid_set
        
