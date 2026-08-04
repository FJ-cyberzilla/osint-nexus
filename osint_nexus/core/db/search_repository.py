from __future__ import annotations

import logging
from typing import Any

from osint_nexus.core.db.base import DatabaseConnection
from osint_nexus.core.exceptions import DatabaseError

logger = logging.getLogger("osint_nexus.db.search_repository")


class SearchRepository:
    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

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
            raise DatabaseError(f"Search failed for '{keyword}': {exc}") from exc
