from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from osint_nexus.core.exceptions import DatabaseError

logger = logging.getLogger("osint_nexus.db.health_manager")


class HealthManager:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    async def check(self) -> bool:
        """Verify that the database is accessible and writable."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO results (username, platform, found) VALUES ('__health__', '__test__', 0)"
                )
                await db.commit()
                await db.execute(
                    "DELETE FROM results WHERE username = '__health__' AND platform = '__test__'"
                )
                await db.commit()
            return True
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            raise DatabaseError(f"Database health check failed: {exc}") from exc
