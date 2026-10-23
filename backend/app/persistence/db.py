"""SQLite database initialization and connection management."""

import aiosqlite
from ..config import settings

INIT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    definition JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL,
    enable_trsm BOOLEAN NOT NULL,
    task TEXT NOT NULL,
    summary JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    parent_event_id TEXT,
    actor_id TEXT NOT NULL,
    target_id TEXT,
    event_type TEXT NOT NULL,
    policy_decision TEXT,
    reason_code TEXT,
    duration_ms REAL,
    payload JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    """Initialize database tables."""
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.executescript(INIT_SCHEMA_SQL)
        await db.commit()
