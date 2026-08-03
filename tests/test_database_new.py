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
        "cache",
        "content_search",
        "sqlite_sequence",
    }

    for table in ["results", "schema_version", "entities", "pivots", "avatars", "historical_scans", "cache", "content_search"]:
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
            assert row is not None and row[0] == 3

        # Check if new tables exist
        for table in ["entities", "cache", "content_search"]:
            async with db.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'") as cur:
                assert await cur.fetchone() is not None

@pytest.mark.asyncio
async def test_database_refactor_features(tmp_path):
    db_path = tmp_path / "test.db"
    db_manager = DatabaseManager(db_path=str(db_path))
    await db_manager.ensure_initialized()

    # Test Cache
    await db_manager.set_cached("test_key", "test_value")
    cached = await db_manager.get_cached("test_key")
    assert cached["value"] == "test_value"

    # Test FTS5 Search
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("INSERT INTO content_search (url, title, body, domain) VALUES (?, ?, ?, ?)",
                         ("http://test.com", "Test Title", "Test body content", "test.com"))
        await db.commit()
    
    results = await db_manager.search("body")
    assert len(results) == 1
    assert "<b>body</b>" in results[0]["body"]

    # Test Batch Insert
    await db_manager.save_batch("INSERT INTO results (username, platform, found) VALUES (?, ?, ?)",
                                [("u1", "p1", 1), ("u2", "p2", 0)])
    
    # Query results to verify batch
    results = await db_manager.query_results(username="u1")
    assert len(results) == 1
    assert results[0]["username"] == "u1"
    
    results = await db_manager.query_results(username="u2")
    assert len(results) == 1
    assert results[0]["username"] == "u2"
