"""Asynchronous structured audit event collector backed by SQLite persistence."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..persistence.event_repository import EventRepository
from ..schemas.events import AuditEvent, AuditEventType
from ..schemas.policy import PolicyDecisionEnum
from ..schemas.provenance import TrustLabel
from .redaction import RedactionEngine

# In-memory fast cache for live runs
_AUDIT_STORE: List[AuditEvent] = []


class AuditEventCollector:
    """Collects, sanitizes, and persists structured causal audit events."""

    def __init__(self, event_repo: Optional[EventRepository] = None):
        self.redaction = RedactionEngine()
        self.event_repo = event_repo or EventRepository()

    async def emit(
        self,
        run_id: str,
        trace_id: str,
        actor_id: str,
        event_type: AuditEventType,
        target_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        policy_decision: Optional[PolicyDecisionEnum] = None,
        reason_code: Optional[str] = None,
        duration_ms: Optional[float] = None,
        trust_labels: Optional[List[TrustLabel]] = None,
        safe_payload_summary: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Create, sanitize, cache, and persist an audit event."""
        sanitized_summary = (
            self.redaction.redact(safe_payload_summary) if safe_payload_summary else None
        )

        event = AuditEvent(
            event_id=str(uuid4()),
            run_id=run_id,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            actor_id=actor_id,
            target_id=target_id,
            event_type=event_type,
            policy_decision=policy_decision,
            reason_code=reason_code,
            duration_ms=duration_ms,
            trust_labels=trust_labels or [],
            safe_payload_summary=sanitized_summary,
            payload_metadata=payload_metadata or {},
            timestamp=datetime.now(timezone.utc),
        )

        _AUDIT_STORE.append(event)

        # Persist to SQLite
        try:
            await self.event_repo.save_event(event)
        except Exception:
            # Fall back to in-memory store if SQLite is temporarily locked or in mock test
            pass

        return event

    def get_events_for_run(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Synchronous in-memory lookup for fast evaluation loops."""
        results = [e for e in _AUDIT_STORE if e.run_id == run_id]
        if event_type:
            results = [e for e in results if e.event_type.value == event_type]
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        return results

    async def get_events_for_run_async(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        policy_decision: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Persistent query from SQLite event repository."""
        events = await self.event_repo.get_events(
            run_id=run_id,
            event_type=event_type,
            actor_id=actor_id,
            policy_decision=policy_decision,
        )
        if not events:
            # Fall back to in-memory store if not yet in SQLite
            return self.get_events_for_run(run_id, event_type, actor_id)
        return events
