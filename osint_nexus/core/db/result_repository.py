from __future__ import annotations

import logging
from typing import Any

from osint_nexus.core.db.base import DatabaseConnection

logger = logging.getLogger("osint_nexus.db.result_repository")


class ResultRepository:
    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    async def save(self, username: str, platform: str, found: bool) -> None:
        try:
            async with self.connection.connect() as db:
                await db.execute(
                    "INSERT INTO results (username, platform, found) VALUES (?, ?, ?)",
                    (username, platform, int(found)),
                )
                await db.commit()
        except Exception as exc:
            logger.error("Failed to save result: %s", exc, exc_info=True)

    async def save_batch(self, query: str, data: list[tuple[Any, ...]]) -> None:
        try:
            async with self.connection.connect() as db:
                await db.executemany(query, data)
                await db.commit()
        except Exception as exc:
            logger.error("Failed to perform batch insert: %s", exc, exc_info=True)

    async def query(
        self,
        username: str | None = None,
        platform: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT id, username, platform, found, timestamp FROM results WHERE 1=1"
        params: list[Any] = []
        if username:
            query += " AND username = ?"
            params.append(username)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            async with self.connection.connect() as db, db.execute(query, params) as cur:
                rows = await cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Query failed: %s", exc, exc_info=True)
            return []
