"""
Asynchronous database management for OSINT Nexus.

Provides persistent storage for scan results with aiosqlite optimisations,
native async support, and schema migration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import aiosqlite

from osint_nexus.core.bootstrap import DATABASE_PATH
from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.database")


class DatabaseManager:
    """
    Manages SQLite storage for OSINT scan results using aiosqlite.

    Attributes:
        db_path: Path to the SQLite database file.
        config: Optional configuration for custom settings.

    Features:
    - Automatic schema creation with versioning.
    - Natively asynchronous save/query methods.
    - Health check for hierarchy integration.
    """

    def __init__(self, config: Config | None = None, db_path: str | None = None) -> None:
        self.config = config or Config()
        custom_path = db_path or getattr(self.config, "DB_PATH", str(DATABASE_PATH))
        self.db_path = Path(str(custom_path)).resolve()

    async def _init_db(self) -> None:
        """Set up initial database schema with versioning."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")

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

            await db.commit()

    async def ensure_initialized(self) -> None:
        """Ensure the database is initialized."""
        await self._init_db()

    # ------------------------------------------------------------------
    # Asynchronous public API
    # ------------------------------------------------------------------

    async def save_result(self, username: str, platform: str, found: bool) -> None:
        """Persist a scan result asynchronously."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO results (username, platform, found) VALUES (?, ?, ?)",
                    (username, platform, int(found)),
                )
                await db.commit()
            logger.debug("Saved result: %s / %s = %s", username, platform, found)
        except Exception as exc:
            logger.error("Failed to save result: %s", exc, exc_info=True)

    async def query_results(
        self,
        username: str | None = None,
        platform: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query stored results with optional filters."""
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
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cur:
                    rows = await cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as exc:
            logger.error("Query failed: %s", exc, exc_info=True)
            return []

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
