from __future__ import annotations

import logging
from typing import TypedDict

from osint_nexus.core.database import DatabaseManager
from osint_nexus.core.types import JSONObject

logger = logging.getLogger("osint_nexus.core.diff")


class Change(TypedDict):
    platform: str
    field: str


class PlatformChanges(TypedDict):
    new_platforms: list[str]
    removed_platforms: list[str]


class DiffResult(TypedDict):
    new_platforms: list[str]
    removed_platforms: list[str]
    modified_content: list[Change]


class DiffEngine:
    """
    Detects changes between current scan results and historical data.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    async def diff(self, username: str, current_results: list[JSONObject]) -> DiffResult:
        """
        Compare current results against the last known state from the database.
        """
        historical_results = await self.db_manager.query_results(username=username, limit=100)
        last_known = self._get_found_results(historical_results)
        current_found = self._get_found_results(current_results)

        platform_changes = self._calculate_platform_changes(current_found, last_known)
        modified_content = self._calculate_content_changes(current_found, last_known)

        diff: DiffResult = {
            "new_platforms": platform_changes["new_platforms"],
            "removed_platforms": platform_changes["removed_platforms"],
            "modified_content": modified_content,
        }

        logger.debug("Diff found: %s", diff)
        return diff

    def _get_found_results(self, results: list[JSONObject]) -> dict[str, JSONObject]:
        # Keep only entries with a truthy "found" flag and index by platform name.
        return {r["platform"]: r for r in results if r.get("found")}

    def _calculate_platform_changes(
        self, current: dict[str, JSONObject], last_known: dict[str, JSONObject]
    ) -> PlatformChanges:
        current_keys = set(current.keys())
        last_keys = set(last_known.keys())
        return {
            "new_platforms": list(current_keys - last_keys),
            "removed_platforms": list(last_keys - current_keys),
        }

    def _calculate_content_changes(
        self, current: dict[str, JSONObject], last_known: dict[str, JSONObject]
    ) -> list[Change]:
        changes: list[Change] = []
        for platform, res in current.items():
            if platform in last_known:
                self._check_result_diff(platform, res, last_known[platform], changes)
        return changes

    def _check_result_diff(
        self, platform: str, new_res: JSONObject, old_res: JSONObject, changes: list[Change]
    ) -> None:
        for field in ("bio", "avatar_url"):
            if new_res.get(field) != old_res.get(field):
                field_name = "avatar" if field == "avatar_url" else field
                changes.append({"platform": platform, "field": field_name})
