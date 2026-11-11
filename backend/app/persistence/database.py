import sqlite3
import os
from pathlib import Path

DEFAULT_DB_PATH = os.environ.get("TRSM_DB_PATH", str(Path(__file__).parent.parent.parent.parent / "trsm.db"))

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH):
    """
    Initializes the SQLite schema for audit events and workflow persistence.
    """
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                trace_id TEXT NOT NULL,
                parent_event_id TEXT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                target_id TEXT,
                source_type TEXT NOT NULL,
                trust_labels TEXT,
                policy_decision TEXT,
                reason_code TEXT,
                policy_version TEXT,
                duration_ms REAL,
                safe_payload_summary TEXT,
                payload_reference TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_run_id ON audit_events(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_actor_id ON audit_events(actor_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_event_type ON audit_events(event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_policy_decision ON audit_events(policy_decision)")
    conn.close()

