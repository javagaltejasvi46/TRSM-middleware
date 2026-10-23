"""FastAPI route dependencies."""

from typing import AsyncGenerator
import aiosqlite
from ..config import settings


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Dependency for providing database connection."""
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
