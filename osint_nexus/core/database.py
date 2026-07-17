"""
Asynchronous database management for OSINT Nexus.

Provides persistent storage for scan results with optional SQLite
optimisations, thread‑safe async wrappers, and schema migration.
Integrates with the HierarchyManager through a health check interface.
"""
from __future__ import annotations

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.database")


class DatabaseManager:
    """
    Manages SQLite storage for OSINT scan results.

    Attributes:
        db_path: Path to the SQLite database file.
        config: Optional configuration for custom settings.

    Features:
    - Automatic schema creation with versioning.
    - Asynchronous save/query methods to avoid blocking the event loop.
    - Connection pooling via a thread‑safe executor (sqlite3 in WAL mode).
    - Health check for hierarchy integration.
    - Backward‑compatible `save_result()` now async (update agent calls to await).
    """

    def __init__(self, config: Optional[Config] = None, db_path: Optional[str] = None) -> None:
        self.config = config or Config()
        custom_path = db_path or getattr(self.config, "DB_PATH", "osint_results.db")
        self.db_path = Path(custom_path).resolve()
        self._init_lock = asyncio.Lock()

        # Use WAL mode for better concurrency
        self._connection_kwargs: Dict[str, Any] = {
            "database": str(self.db_path),
            "check_same_thread": False,  # we manage thread safety ourselves
        }
        # Initialise schema synchronously (runs once in constructor)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new connection with WAL mode enabled."""
        conn = sqlite3.connect(**self._connection_kwargs)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Set up initial database schema with versioning."""
        try:
            with self._get_connection() as conn:
                # Create results table (original schema)
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS results ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "username TEXT NOT NULL,"
                    "platform TEXT NOT NULL,"
                    "found INTEGER NOT NULL,"
                    "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
                # Schema versioning table
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS schema_version ("
                    "version INTEGER PRIMARY KEY,"
                    "applied_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    ")"
                )
                cur = conn.execute("SELECT MAX(version) FROM schema_version")
                row = cur.fetchone()
                current_version = row[0] if row and row[0] else 0
                if current_version < 1:
                    conn.execute("INSERT INTO schema_version (version) VALUES (1)")
                conn.commit()
        except sqlite3.Error as exc:
            logger.critical("Failed to initialise database: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Asynchronous public API
    # ------------------------------------------------------------------

    async def save_result(self, username: str, platform: str, found: bool) -> None:
        """
        Persist a scan result asynchronously.

        Args:
            username: The target username.
            platform: The platform name.
            found: Whether the username was detected.

        Note:
            This method is now async. Callers should use `await`.
        """
        try:
            await asyncio.to_thread(
                self._save_sync, username, platform, int(found)
            )
            logger.debug("Saved result: %s / %s = %s", username, platform, found)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to save result: %s", exc, exc_info=True)

    async def query_results(
        self,
        username: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query stored results with optional filters.

        Args:
            username: Filter by username (exact match).
            platform: Filter by platform name (exact match).
            limit: Maximum number of rows to return.

        Returns:
            List of dictionaries with keys: id, username, platform, found, timestamp.
        """
        query = "SELECT id, username, platform, found, timestamp FROM results WHERE 1=1"
        params: list = []
        if username:
            query += " AND username = ?"
            params.append(username)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        def _query_sync() -> List[Dict[str, Any]]:
            with self._get_connection() as conn:
                rows = conn.execute(query, params).fetchall()
                return [dict(row) for row in rows]

        try:
            return await asyncio.to_thread(_query_sync)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Query failed: %s", exc, exc_info=True)
            return []

    async def health_check(self) -> bool:
        """
        Verify that the database is accessible and writable.

        Returns:
            True if healthy.
        """
        try:
            await asyncio.to_thread(self._health_check_sync)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Database health check failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Synchronous helpers (run inside thread executor)
    # ------------------------------------------------------------------

    def _save_sync(self, username: str, platform: str, found: int) -> None:
        """Synchronous insert (run in thread pool)."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO results (username, platform, found) VALUES (?, ?, ?)",
                (username, platform, found),
            )
            conn.commit()

    def _health_check_sync(self) -> None:
        """Quick insert/delete test to confirm database is writable."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO results (username, platform, found) VALUES ('__health__', '__test__', 0)"
            )
            conn.commit()
            conn.execute(
                "DELETE FROM results WHERE username = '__health__' AND platform = '__test__'"
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Legacy compatibility (synchronous wrapper)
    # ------------------------------------------------------------------

    def save_result_sync(self, username: str, platform: str, found: bool) -> None:
        """
        Synchronous save for non‑async contexts (deprecated).

        Prefer `await save_result()` in async code.
        """
        self._save_sync(username, platform, int(found))
