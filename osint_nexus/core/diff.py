"""
Diff Engine for detecting changes in identity presence.

Compares current scan results against historical database records to identify
changes in platform presence and content.
"""

from __future__ import annotations

import logging
from typing import Any

from osint_nexus.core.database import DatabaseManager

logger = logging.getLogger("osint_nexus.core.diff")


class DiffEngine:
    """
    Detects changes between current scan results and historical data.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    async def diff(self, username: str, current_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Compare current results against the last known state from the database.
        """
        historical_results = await self.db_manager.query_results(username=username, limit=100)
        last_known = self._get_found_results(historical_results)
        current_found = self._get_found_results(current_results)

        diff = self._calculate_platform_changes(current_found, last_known)
        diff["modified_content"] = self._calculate_content_changes(current_found, last_known)

        logger.debug("Diff found: %s", diff)
        return diff

    def _get_found_results(self, results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {r["platform"]: r for r in results if r.get("found")}

    def _calculate_platform_changes(self, current: dict[str, Any], last_known: dict[str, Any]) -> dict[str, Any]:
        current_keys = set(current.keys())
        last_keys = set(last_known.keys())
        return {
            "new_platforms": list(current_keys - last_keys),
            "removed_platforms": list(last_keys - current_keys),
        }

    def _calculate_content_changes(self, current: dict[str, Any], last_known: dict[str, Any]) -> list[dict[str, str]]:
        changes: list[dict[str, str]] = []
        for platform, res in current.items():
            if platform in last_known:
                self._check_result_diff(platform, res, last_known[platform], changes)
        return changes

    def _check_result_diff(self, platform: str, new_res: dict[str, Any], old_res: dict[str, Any], changes: list[dict[str, str]]) -> None:
        for field in ("bio", "avatar_url"):
            if new_res.get(field) != old_res.get(field):
                field_name = "avatar" if field == "avatar_url" else field
                changes.append({"platform": platform, "field": field_name})
