from __future__ import annotations

from osint_nexus.core.db.base import DatabaseConnection


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
