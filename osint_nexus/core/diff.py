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
        # Fetch last results from DB
        historical_results = await self.db_manager.query_results(username=username, limit=100)

        # Determine last known found state
        last_known_results = {r["platform"]: r for r in historical_results if r.get("found")}

        # Current found platforms
        current_found = {r["platform"]: r for r in current_results if r.get("found")}

        diff = {
            "new_platforms": list(set(current_found.keys()) - set(last_known_results.keys())),
            "removed_platforms": list(set(last_known_results.keys()) - set(current_found.keys())),
            "modified_content": [],
        }

        # Check for content changes (e.g. bio, profile picture)
        for platform, res in current_found.items():
            if platform in last_known_results:
                old_res = last_known_results[platform]
                # Compare critical fields if available
                if res.get("bio") != old_res.get("bio"):
                    diff["modified_content"].append({"platform": platform, "field": "bio"})
                if res.get("avatar_url") != old_res.get("avatar_url"):
                    diff["modified_content"].append({"platform": platform, "field": "avatar"})

        logger.debug("Diff found: %s", diff)
        return diff
