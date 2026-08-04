from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import aiosqlite

if TYPE_CHECKING:
    pass


@runtime_checkable
class DatabaseProtocol(Protocol):
    def connect(self) -> AbstractAsyncContextManager[aiosqlite.Connection]: ...
    async def close(self) -> None: ...


class DatabaseConnection(DatabaseProtocol):
    """Manages a persistent connection to the SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get or initialize the persistent connection."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[aiosqlite.Connection]:
        """Provides access to the persistent database connection."""
        db = await self._get_connection()
        yield db

    async def close(self) -> None:
        """Closes the persistent database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
