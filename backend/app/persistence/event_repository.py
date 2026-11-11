import json
import sqlite3
from typing import List, Optional
from backend.app.contracts.events import AuditEvent
from backend.app.persistence.database import get_connection, DEFAULT_DB_PATH

class EventRepository:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def insert_event(self, event: AuditEvent):
        conn = get_connection(self.db_path)
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO audit_events (
                    event_id, run_id, trace_id, parent_event_id, timestamp,
                    event_type, actor_id, target_id, source_type, trust_labels,
                    policy_decision, reason_code, policy_version,
                    duration_ms, safe_payload_summary, payload_reference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.trace_id,
                    event.parent_event_id,
                    event.timestamp,
                    event.event_type,
                    event.actor_id,
                    event.target_id,
                    event.source_type,
                    json.dumps(event.trust_labels),
                    event.policy_decision,
                    event.reason_code,
                    event.policy_version,
                    event.duration_ms,
                    event.safe_payload_summary,
                    json.dumps(event.payload_reference or {})
                )
            )
        conn.close()

    def get_event(self, event_id: str) -> Optional[AuditEvent]:
        conn = get_connection(self.db_path)
        cursor = conn.execute("SELECT * FROM audit_events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_event(row)

    def list_events(
        self,
        run_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        event_type: Optional[str] = None,
        policy_decision: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []

        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if actor_id:
            query += " AND actor_id = ?"
            params.append(actor_id)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if policy_decision:
            query += " AND policy_decision = ?"
            params.append(policy_decision)

        query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = get_connection(self.db_path)
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row: sqlite3.Row) -> AuditEvent:
        trust_labels = []
        if row["trust_labels"]:
            try:
                trust_labels = json.loads(row["trust_labels"])
            except Exception:
                trust_labels = []

        payload_ref = {}
        if row["payload_reference"]:
            try:
                payload_ref = json.loads(row["payload_reference"])
            except Exception:
                payload_ref = {}

        return AuditEvent(
            event_id=row["event_id"],
            run_id=row["run_id"],
            trace_id=row["trace_id"],
            parent_event_id=row["parent_event_id"],
            timestamp=row["timestamp"],
            event_type=row["event_type"],
            actor_id=row["actor_id"],
            target_id=row["target_id"],
            source_type=row["source_type"],
            trust_labels=trust_labels,
            policy_decision=row["policy_decision"],
            reason_code=row["reason_code"],
            policy_version=row["policy_version"],
            duration_ms=row["duration_ms"],
            safe_payload_summary=row["safe_payload_summary"],
            payload_reference=payload_ref
        )

event_repository = EventRepository()

