from __future__ import annotations

import logging
from typing import Any

from osint_nexus.core.db.base import DatabaseConnection

logger = logging.getLogger("osint_nexus.db.cache_repository")


class CacheRepository:
    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    async def get(self, key: str) -> dict[str, Any] | None:
        try:
            async with self.connection.connect() as db:
                cursor = await db.execute(
                    "SELECT * FROM cache WHERE key = ? AND expires_at > datetime('now')", (key,)
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as exc:
            logger.error("Failed to get cache: %s", exc, exc_info=True)
            return None

    async def set(self, key: str, value: str, ttl_days: int = 1) -> None:
        try:
            async with self.connection.connect() as db:
                await db.execute(
                    f"INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, datetime('now', '+{ttl_days} day'))",
                    (key, value),
                )
                await db.commit()
        except Exception as exc:
            logger.error("Failed to set cache: %s", exc, exc_info=True)
