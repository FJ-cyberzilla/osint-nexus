"""
Compliance and PII Redaction module.

Provides automated data scrubbing rules to sanitize unintended PII
prior to persistent storage or reporting.
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

logger = logging.getLogger("osint_nexus.core.compliance")


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

    def sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Scans a data dictionary and replaces detected PII with '[REDACTED]'.

        Args:
            data: The input dictionary containing scan results.

        Returns:
            A sanitized dictionary with PII redacted.
        """
        sanitized = data.copy()

        # Recursive function to handle nested dicts/lists
        def _scrub(item: Any) -> Any:
            """
            Recursively scans an item and redacts PII if found.
            """
            if isinstance(item, dict):
                return {k: _scrub(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [_scrub(i) for i in item]
            elif isinstance(item, str):
                for p_type, pattern in self.redaction_patterns.items():
                    if pattern.search(item):
                        logger.info("Redacting PII of type: %s", p_type)
                        return "[REDACTED]"
            return item

        return cast(dict[str, Any], _scrub(sanitized))
