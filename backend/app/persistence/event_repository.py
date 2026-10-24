"""Repository for persisting and querying structured audit events via SQLite."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from ..schemas.events import AuditEvent, AuditEventType
from ..schemas.policy import PolicyDecisionEnum
from ..schemas.provenance import TrustLabel
from .db import get_connection, init_db


class EventRepository:
    """Provides SQLite persistence and filtering for audit events."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    async def _ensure_db(self):
        await init_db(self.db_path)

    async def save_event(self, event: AuditEvent) -> AuditEvent:
        """Persist a single audit event to SQLite."""
        await self._ensure_db()
        trust_labels_json = json.dumps([t.value for t in event.trust_labels])
        payload_meta_json = json.dumps(event.payload_metadata)
        decision_val = event.policy_decision.value if event.policy_decision else None
        event_type_val = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        ts_val = event.timestamp.isoformat() if event.timestamp else datetime.now(timezone.utc).isoformat()

        async with get_connection(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO audit_events (
                    event_id, run_id, trace_id, parent_event_id, actor_id, target_id,
                    event_type, policy_decision, reason_code, duration_ms,
                    trust_labels, safe_payload_summary, payload_metadata, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.trace_id,
                    event.parent_event_id,
                    event.actor_id,
                    event.target_id,
                    event_type_val,
                    decision_val,
                    event.reason_code,
                    event.duration_ms,
                    trust_labels_json,
                    event.safe_payload_summary,
                    payload_meta_json,
                    ts_val,
                ),
            )
            await db.commit()
        return event

    async def get_events(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        policy_decision: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Query audit events for a given run with optional filters."""
        await self._ensure_db()
        query = "SELECT * FROM audit_events WHERE run_id = ?"
        params: List[Any] = [run_id]

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if actor_id:
            query += " AND actor_id = ?"
            params.append(actor_id)
        if policy_decision:
            query += " AND policy_decision = ?"
            params.append(policy_decision)

        query += " ORDER BY timestamp ASC"

        async with get_connection(self.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            events = []
            for row in rows:
                raw_labels = json.loads(row["trust_labels"]) if row["trust_labels"] else []
                trust_labels = [TrustLabel(lbl) for lbl in raw_labels if lbl in TrustLabel._value2member_map_]
                meta = json.loads(row["payload_metadata"]) if row["payload_metadata"] else {}
                decision = PolicyDecisionEnum(row["policy_decision"]) if row["policy_decision"] else None
                event_type_enum = AuditEventType(row["event_type"]) if row["event_type"] in AuditEventType._value2member_map_ else AuditEventType.RESOURCE_EXECUTED
                ts = datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else datetime.now(timezone.utc)

                events.append(
                    AuditEvent(
                        event_id=row["event_id"],
                        run_id=row["run_id"],
                        trace_id=row["trace_id"],
                        parent_event_id=row["parent_event_id"],
                        actor_id=row["actor_id"],
                        target_id=row["target_id"],
                        event_type=event_type_enum,
                        policy_decision=decision,
                        reason_code=row["reason_code"],
                        duration_ms=row["duration_ms"],
                        trust_labels=trust_labels,
                        safe_payload_summary=row["safe_payload_summary"],
                        payload_metadata=meta,
                        timestamp=ts,
                    )
                )
            return events
