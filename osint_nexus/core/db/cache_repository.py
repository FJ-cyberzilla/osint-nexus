from __future__ import annotations

import logging

from osint_nexus.core.db.base import DatabaseEngine
from osint_nexus.core.exceptions import DatabaseError
from osint_nexus.core.type_defs import JSONObject

logger = logging.getLogger("osint_nexus.db.cache_repository")


class CacheRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    async def get(self, key: str) -> JSONObject | None:
        try:
            return await self.engine.fetchone(
                "SELECT * FROM cache WHERE key = ? AND expires_at > datetime('now')", (key,)
            )
        except Exception as exc:
            logger.error("Failed to get cache: %s", exc, exc_info=True)
            raise DatabaseError(f"Cache get failed: {exc}") from exc

    async def set(self, key: str, value: str, ttl_days: int = 1) -> None:
        try:
            await self.engine.execute(
                f"INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, datetime('now', '+{ttl_days} day'))",
                (key, value),
            )
        except Exception as exc:
            logger.error("Failed to set cache: %s", exc, exc_info=True)
            raise DatabaseError(f"Cache set failed: {exc}") from exc
