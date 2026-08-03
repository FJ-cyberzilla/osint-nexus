"""
Asynchronous database management for OSINT Nexus.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite

from osint_nexus.core.bootstrap import DATABASE_PATH
from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.database")


class DatabaseConnection:
    """Manages connections to the SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[aiosqlite.Connection]:
        """Provides an async context manager for database connections."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")
            db.row_factory = aiosqlite.Row
            yield db


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


class SchemaManager:
    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    async def initialize(self) -> None:
        """Set up initial database schema with versioning."""
        async with self.connection.connect() as db:
            # Schema versioning table
            await db.execute(
                "CREATE TABLE IF NOT EXISTS schema_version ("
                "version INTEGER PRIMARY KEY,"
                "applied_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                ")"
            )

            async with db.execute("SELECT MAX(version) FROM schema_version") as cur:
                row = await cur.fetchone()
                current_version = row[0] if row and row[0] else 0

            if current_version < 1:
                # Create results table
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS results ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "username TEXT NOT NULL,"
                    "platform TEXT NOT NULL,"
                    "found INTEGER NOT NULL,"
                    "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
                await db.execute("INSERT INTO schema_version (version) VALUES (1)")
                current_version = 1

            if current_version < 2:
                # Phase 1: Modernization Tables
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS entities ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "main_username TEXT UNIQUE NOT NULL,"
                    "display_name TEXT,"
                    "bio TEXT,"
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS pivots ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "entity_id INTEGER,"
                    "type TEXT NOT NULL,"
                    "value TEXT NOT NULL,"
                    "source_platform TEXT,"
                    "FOREIGN KEY (entity_id) REFERENCES entities(id)"
                    ")"
                )
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS avatars ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "entity_id INTEGER,"
                    "platform TEXT NOT NULL,"
                    "url TEXT,"
                    "phash TEXT,"
                    "last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,"
                    "FOREIGN KEY (entity_id) REFERENCES entities(id)"
                    ")"
                )
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS historical_scans ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "username TEXT NOT NULL,"
                    "platform TEXT NOT NULL,"
                    "found INTEGER NOT NULL,"
                    "content_hash TEXT,"
                    "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
                await db.execute("INSERT INTO schema_version (version) VALUES (2)")
                current_version = 2

            if current_version < 3:
                # Cache table
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY,value TEXT,expires_at DATETIME)"
                )
                # FTS5 table
                await db.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS content_search USING fts5(
                        url, title, body, domain
                    )
                """)
                await db.execute("INSERT INTO schema_version (version) VALUES (3)")
                current_version = 3

            await db.commit()


class DatabaseManager:
    """
    Manages SQLite storage for OSINT scan results using aiosqlite.
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
