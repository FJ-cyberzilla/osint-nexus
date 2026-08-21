from __future__ import annotations

import logging

from osint_nexus.core.db.base import DatabaseEngine
from osint_nexus.core.exceptions import DatabaseError
from osint_nexus.core.type_defs import JSONObject

logger = logging.getLogger("osint_nexus.db.search_repository")


class SearchRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine: DatabaseEngine = engine

    async def search(self, keyword: str) -> list[JSONObject]:
        """Perform FTS5 search."""
        try:
            return await self.engine.fetchall(
                "SELECT url, title, snippet(content_search, 2, '<b>', '</b>', '...', 10) as body FROM content_search WHERE content_search MATCH ?",
                (keyword,),
            )
        except Exception as exc:
            logger.error("Search failed: %s", exc, exc_info=True)
            raise DatabaseError(f"Search failed for '{keyword}': {exc}") from exc
