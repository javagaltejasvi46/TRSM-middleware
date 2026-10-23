"""Asynchronous structured audit event collector."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..schemas.events import AuditEvent, AuditEventType
from ..schemas.policy import PolicyDecisionEnum
from ..schemas.provenance import TrustLabel
from .redaction import RedactionEngine

# In-memory storage for MVP, backed by SQLite / repository
_AUDIT_STORE: List[AuditEvent] = []


class AuditEventCollector:
    """Collects and stores structured causal audit events."""

    def __init__(self):
        self.redaction = RedactionEngine()

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
        """Create, sanitize, and store an audit event."""
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
        return event

    def get_events_for_run(
        self,
        run_id: str,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> List[AuditEvent]:
        """Query events for a run with optional filtering."""
        results = [e for e in _AUDIT_STORE if e.run_id == run_id]
        if event_type:
            results = [e for e in results if e.event_type.value == event_type]
        if actor_id:
            results = [e for e in results if e.actor_id == actor_id]
        return results
