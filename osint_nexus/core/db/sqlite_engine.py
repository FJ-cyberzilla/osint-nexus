from __future__ import annotations

from pathlib import Path
from typing import Any

import aiosqlite

from osint_nexus.core.type_defs import JSONValue

from .base import DatabaseEngine


class SQLiteEngine(DatabaseEngine):
    """SQLite backend engine."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.row_factory = aiosqlite.Row

    async def execute(self, query: str, params: tuple[JSONValue, ...] = ()) -> None:
        if not self._connection:
            await self.connect()
        await self._connection.execute(query, params)
        await self._connection.commit()

    async def executemany(self, query: str, params: list[tuple[JSONValue, ...]]) -> None:
        if not self._connection:
            await self.connect()
        await self._connection.executemany(query, params)
        await self._connection.commit()

    async def fetchall(self, query: str, params: tuple[JSONValue, ...] = ()) -> list[dict[str, Any]]:
        if not self._connection:
            await self.connect()
        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def fetchone(self, query: str, params: tuple[JSONValue, ...] = ()) -> dict[str, Any] | None:
        if not self._connection:
            await self.connect()
        async with self._connection.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
