"""
Compliance and PII Redaction module.

Provides automated data scrubbing rules to sanitize unintended PII
prior to persistent storage or reporting.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import cast, overload

logger = logging.getLogger("osint_nexus.core.compliance")

type Scrubbable = Mapping[str, "Scrubbable"] | Sequence["Scrubbable"] | str | int | float | bool | None


class ComplianceEngine:
    """
    Handles PII redaction and compliance scrubbing.
    """

    def __init__(self) -> None:
        # Simple patterns for PII detection; can be expanded
        self.redaction_patterns = {
            "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
            "phone": re.compile(
                r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
            ),
        }

    @overload
    def sanitize(self, data: Mapping[str, Scrubbable]) -> Mapping[str, Scrubbable]: ...

    @overload
    def sanitize(self, data: Sequence[Scrubbable]) -> Sequence[Scrubbable]: ...

    def sanitize(
        self, data: Mapping[str, Scrubbable] | Sequence[Scrubbable]
    ) -> Mapping[str, Scrubbable] | Sequence[Scrubbable]:
        """
        Scans a data structure and replaces detected PII with '[REDACTED]'.

        Args:
            data: The input dictionary or list containing scan results.

        Returns:
            A sanitized data structure with PII redacted.
        """

        # Recursive function to handle nested dicts/lists
        def _scrub(item: Scrubbable) -> Scrubbable:
            """
            Recursively scans an item and redacts PII if found.
            """
            if isinstance(item, Mapping):
                return {k: _scrub(v) for k, v in item.items()}
            elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
                return [_scrub(i) for i in item]
            elif isinstance(item, str):
                for p_type, pattern in self.redaction_patterns.items():
                    if pattern.search(item):
                        logger.info("Redacting PII of type: %s", p_type)
                        return "[REDACTED]"
            return item

        # Cast to match the expected return type structure
        return cast(Mapping[str, Scrubbable] | Sequence[Scrubbable], _scrub(data))
