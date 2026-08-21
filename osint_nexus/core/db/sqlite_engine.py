from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite

from osint_nexus.core.type_defs import JSONValue

from .base import DatabaseEngine

if TYPE_CHECKING:
    from osint_nexus.core.type_defs import MetadataDict


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
        if self._connection is None:
            await self.connect()
        assert self._connection is not None
        await self._connection.execute(query, params)
        await self._connection.commit()

    async def executemany(self, query: str, params: list[tuple[JSONValue, ...]]) -> None:
        if self._connection is None:
            await self.connect()
        assert self._connection is not None
        await self._connection.executemany(query, params)
        await self._connection.commit()

    async def fetchall(self, query: str, params: tuple[JSONValue, ...] = ()) -> list[MetadataDict]:
        if self._connection is None:
            await self.connect()
        assert self._connection is not None
        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def fetchone(self, query: str, params: tuple[JSONValue, ...] = ()) -> MetadataDict | None:
        if self._connection is None:
            await self.connect()
        assert self._connection is not None
        async with self._connection.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
