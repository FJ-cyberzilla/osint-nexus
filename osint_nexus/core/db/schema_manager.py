from __future__ import annotations

from osint_nexus.core.db.base import DatabaseEngine


class SchemaManager:
    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    async def _migrate_v1(self) -> int:
        # Create results table
        await self.engine.execute(
            "CREATE TABLE IF NOT EXISTS results ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "username TEXT NOT NULL,"
            "platform TEXT NOT NULL,"
            "found INTEGER NOT NULL,"
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        await self.engine.execute("INSERT INTO schema_version (version) VALUES (1)")
        return 1

    async def _migrate_v2(self) -> int:
        # Phase 1: Modernization Tables
        await self.engine.execute(
            "CREATE TABLE IF NOT EXISTS entities ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "main_username TEXT UNIQUE NOT NULL,"
            "display_name TEXT,"
            "bio TEXT,"
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        await self.engine.execute(
            "CREATE TABLE IF NOT EXISTS pivots ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "entity_id INTEGER,"
            "type TEXT NOT NULL,"
            "value TEXT NOT NULL,"
            "source_platform TEXT,"
            "FOREIGN KEY (entity_id) REFERENCES entities(id)"
            ")"
        )
        await self.engine.execute(
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
        await self.engine.execute(
            "CREATE TABLE IF NOT EXISTS historical_scans ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "username TEXT NOT NULL,"
            "platform TEXT NOT NULL,"
            "found INTEGER NOT NULL,"
            "content_hash TEXT,"
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        await self.engine.execute("INSERT INTO schema_version (version) VALUES (2)")
        return 2

    async def _migrate_v3(self) -> int:
        # Cache table
        await self.engine.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY,value TEXT,expires_at DATETIME)"
        )
        # FTS5 table
        await self.engine.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS content_search USING fts5(
                url, title, body, domain
            )
        """)
        await self.engine.execute("INSERT INTO schema_version (version) VALUES (3)")
        return 3

    async def initialize(self) -> None:
        """Set up initial database schema with versioning."""
        await self._ensure_version_table()
        current_version = await self._get_current_version()
        await self._run_migrations(current_version)

    async def _ensure_version_table(self) -> None:
        await self.engine.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "version INTEGER PRIMARY KEY,"
            "applied_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ")"
        )

    async def _get_current_version(self) -> int:
        row = await self.engine.fetchone("SELECT MAX(version) FROM schema_version")
        if row:
            # The result keys are often depending on row factory but `fetchone` returns `dict` now.
            # Select MAX(version) can return dict with key like 'MAX(version)'
            val = list(row.values())[0]
            if isinstance(val, int):
                return val
            if isinstance(val, float):
                return int(val)
            if isinstance(val, str) and val.isdigit():
                return int(val)
        return 0

    async def _run_migrations(self, current_version: int) -> None:
        if current_version < 1:
            current_version = await self._migrate_v1()
        if current_version < 2:
            current_version = await self._migrate_v2()
        if current_version < 3:
            await self._migrate_v3()
