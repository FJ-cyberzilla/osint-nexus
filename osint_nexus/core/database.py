"""
Asynchronous database management for OSINT Nexus.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import aiosqlite

from osint_nexus.core.bootstrap import DATABASE_PATH
from osint_nexus.core.config import Config
from osint_nexus.core.db.base import DatabaseConnection
from osint_nexus.core.db.cache_repository import CacheRepository
from osint_nexus.core.db.result_repository import ResultRepository
from osint_nexus.core.db.schema_manager import SchemaManager

logger = logging.getLogger("osint_nexus.database")


class DatabaseManager:
    """
    Manages SQLite storage for OSINT scan results using aiosqlite.
    Acts as a Facade for various database repositories.
    """

    def __init__(self, config: Config | None = None, db_path: str | None = None) -> None:
        self.config = config or Config()
        custom_path = db_path or getattr(self.config, "DB_PATH", str(DATABASE_PATH))
        self.db_path = Path(str(custom_path)).resolve()
        self.connection = DatabaseConnection(self.db_path)
        self.results = ResultRepository(self.connection)
        self.cache = CacheRepository(self.connection)
        self.schema = SchemaManager(self.connection)

    async def _init_db(self) -> None:
        await self.schema.initialize()

    # --- Delegation for backward compatibility ---

    async def save_result(self, username: str, platform: str, found: bool) -> None:
        await self.results.save(username, platform, found)

    async def save_batch(self, query: str, data: list[tuple[Any, ...]]) -> None:
        await self.results.save_batch(query, data)

    async def get_cached(self, key: str) -> dict[str, Any] | None:
        return await self.cache.get(key)

    async def set_cached(self, key: str, value: str, ttl_days: int = 1) -> None:
        await self.cache.set(key, value, ttl_days)

    async def ensure_initialized(self) -> None:
        """Ensure the database is initialized."""
        await self._init_db()

    async def search(self, keyword: str) -> list[dict[str, Any]]:
        """Perform FTS5 search."""
        try:
            async with self.connection.connect() as db:
                cursor = await db.execute(
                    "SELECT url, title, snippet(content_search, 2, '<b>', '</b>', '...', 10) as body FROM content_search WHERE content_search MATCH ?",
                    (keyword,),
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Search failed: %s", exc, exc_info=True)
            return []

    async def query_results(
        self,
        username: str | None = None,
        platform: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query stored results with optional filters."""
        return await self.results.query(username, platform, limit)

    async def health_check(self) -> bool:
        """Verify that the database is accessible and writable."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO results (username, platform, found) VALUES ('__health__', '__test__', 0)"
                )
                await db.commit()
                await db.execute(
                    "DELETE FROM results WHERE username = '__health__' AND platform = '__test__'"
                )
                await db.commit()
            return True
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            return False
