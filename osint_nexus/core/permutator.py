"""
Username permutation engine for OSINT Nexus.

Generates common variations of target handles to increase scan coverage.
"""

from __future__ import annotations

import re


class Permutator:
    """
    Generates permutations of a given username.

    Common variations include:
    - john_doe -> john.doe, john-doe, johndoe
    - john -> john123, john_
    """

    def __init__(self) -> None:
        pass

    def generate(self, username: str) -> set[str]:
        """
        Generate a set of username permutations.
        """
        permutations = {username}

        # Base username without separators
        clean_username = re.sub(r"[\._-]", "", username)
        permutations.add(clean_username)

        # Split by common separators
        parts = re.split(r"[\._-]", username)
        if len(parts) > 1:
            # Re-join with different separators
            permutations.add(".".join(parts))
            permutations.add("-".join(parts))
            permutations.add("_".join(parts))

        # Add common suffixes if username is short
        if len(username) < 10:
            permutations.add(f"{username}123")
            permutations.add(f"{username}_")

        return permutations
