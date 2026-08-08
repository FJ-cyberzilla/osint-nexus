"""
Asynchronous database management for OSINT Nexus.
"""

from __future__ import annotations

import logging
from pathlib import Path

from osint_nexus.core.bootstrap import DATABASE_PATH
from osint_nexus.core.config import Config
from osint_nexus.core.db.cache_repository import CacheRepository
from osint_nexus.core.db.health_manager import HealthManager
from osint_nexus.core.db.result_repository import ResultRepository
from osint_nexus.core.db.schema_manager import SchemaManager
from osint_nexus.core.db.search_repository import SearchRepository
from osint_nexus.core.db.sqlite_engine import SQLiteEngine
from osint_nexus.core.type_defs import JSONObject, JSONValue

logger = logging.getLogger("osint_nexus.database")


class DatabaseManager:
    """
    Manages database storage for OSINT scan results using an engine.
    Acts as a Facade for various database repositories.
    """

    def __init__(self, config: Config | None = None, db_path: str | None = None) -> None:
        self.config = config or Config()
        custom_path = db_path or getattr(self.config, "DB_PATH", str(DATABASE_PATH))
        self.db_path = Path(str(custom_path)).resolve()
        self.engine = SQLiteEngine(self.db_path)
        self.results = ResultRepository(self.engine)
        self.cache = CacheRepository(self.engine)
        self.schema = SchemaManager(self.engine)
        self.search_repo = SearchRepository(self.engine)
        self.health = HealthManager(self.db_path)

    async def _init_db(self) -> None:
        await self.engine.connect()
        await self.schema.initialize()

    # --- Delegation for backward compatibility ---

    async def save_result(self, username: str, platform: str, found: bool) -> None:
        await self.results.save(username, platform, found)

    async def save_batch(self, query: str, data: list[tuple[JSONValue, ...]]) -> None:
        await self.results.save_batch(query, data)

    async def get_cached(self, key: str) -> JSONObject | None:
        return await self.cache.get(key)

    async def set_cached(self, key: str, value: str, ttl_days: int = 1) -> None:
        await self.cache.set(key, value, ttl_days)

    async def ensure_initialized(self) -> None:
        """Ensure the database is initialized."""
        await self._init_db()

    async def search(self, keyword: str) -> list[JSONObject]:
        """Perform FTS5 search."""
        return await self.search_repo.search(keyword)

    async def query_results(
        self,
        username: str | None = None,
        platform: str | None = None,
        limit: int = 100,
    ) -> list[JSONObject]:
        """Query stored results with optional filters."""
        return await self.results.query(username, platform, limit)

    async def health_check(self) -> bool:
        """Verify that the database is accessible and writable."""
        return await self.health.check()

    async def close(self) -> None:
        """Closes the database connection."""
        await self.engine.close()
