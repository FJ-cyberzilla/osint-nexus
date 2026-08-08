from collections.abc import AsyncGenerator

from osint_nexus.core.database import DatabaseManager


async def get_db() -> AsyncGenerator[DatabaseManager]:
    """Dependency to provide a database manager instance."""
    db = DatabaseManager()
    await db.ensure_initialized()
    try:
        yield db
    finally:
        await db.close()
