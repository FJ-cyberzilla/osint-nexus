from __future__ import annotations

import logging
from typing import cast

from osint_nexus.core.db.base import DatabaseEngine
from osint_nexus.core.type_defs import JSONObject, JSONValue

logger = logging.getLogger("osint_nexus.db.result_repository")


class ResultRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    async def save(self, username: str, platform: str, found: bool) -> None:
        try:
            await self.engine.execute(
                "INSERT INTO results (username, platform, found) VALUES (?, ?, ?)",
                (username, platform, int(found)),
            )
        except Exception as exc:
            logger.error("Failed to save result: %s", exc, exc_info=True)

    async def save_batch(self, query: str, data: list[tuple[JSONValue, ...]]) -> None:
        try:
            await self.engine.executemany(query, data)
        except Exception as exc:
            logger.error("Failed to perform batch insert: %s", exc, exc_info=True)

    async def query(
        self,
        username: str | None = None,
        platform: str | None = None,
        limit: int = 100,
    ) -> list[JSONObject]:
        query = "SELECT id, username, platform, found, timestamp FROM results WHERE 1=1"
        params: list[JSONValue] = []
        if username:
            query += " AND username = ?"
            params.append(username)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            rows = await self.engine.fetchall(query, tuple(params))
            return cast(list[JSONObject], rows)
        except Exception as exc:
            logger.error("Query failed: %s", exc, exc_info=True)
            return []
