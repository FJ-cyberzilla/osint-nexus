from typing import Any

import aiosqlite
import pytest

from osint_nexus.core.database import DatabaseManager


@pytest.mark.asyncio
async def test_database_initialization(tmp_path: Any) -> None:
    db_path = tmp_path / "test.db"
    db_manager = DatabaseManager(db_path=str(db_path))
    await db_manager.ensure_initialized()

    async with (
        aiosqlite.connect(db_path) as db,
        db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cur,
    ):
        tables = {row[0] for row in await cur.fetchall()}

    expected_tables = {
        "results",
        "schema_version",
        "entities",
        "pivots",
        "avatars",
        "historical_scans",
        "sqlite_sequence",
    }

    for table in ["results", "schema_version", "entities", "pivots", "avatars", "historical_scans"]:
        assert table in tables


@pytest.mark.asyncio
async def test_database_migration(tmp_path: Any) -> None:
    db_path = tmp_path / "migration.db"

    # Manually create a version 1 database
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "CREATE TABLE results (id INTEGER PRIMARY KEY, username TEXT, platform TEXT, found INTEGER, timestamp DATETIME)"
        )
        await db.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at DATETIME)")
        await db.execute("INSERT INTO schema_version (version) VALUES (1)")
        await db.commit()

    db_manager = DatabaseManager(db_path=str(db_path))
    await db_manager.ensure_initialized()

    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT MAX(version) FROM schema_version") as cur:
            row = await cur.fetchone()
            assert row is not None and row[0] == 2

        # Check if new tables exist
        async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'") as cur:
            assert await cur.fetchone() is not None
