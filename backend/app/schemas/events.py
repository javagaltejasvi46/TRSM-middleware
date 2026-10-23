"""Structured audit event contracts and event type taxonomy."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from .policy import PolicyDecisionEnum
from .provenance import TrustLabel


class AuditEventType(str, Enum):
    """Categorized event types emitted to the audit pipeline."""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    MESSAGE_PROPOSED = "message.proposed"
    MESSAGE_POLICY_DECIDED = "message.policy_decided"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_BLOCKED = "message.blocked"
    MESSAGE_QUARANTINED = "message.quarantined"
    RESOURCE_PROPOSED = "resource.proposed"
    RESOURCE_POLICY_DECIDED = "resource.policy_decided"
    RESOURCE_EXECUTED = "resource.executed"
    RESOURCE_BLOCKED = "resource.blocked"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    THREAT_DETECTED = "threat.detected"
    REVIEW_REQUESTED = "review.requested"
    REVIEW_RESOLVED = "review.resolved"
    EVALUATION_COMPLETED = "evaluation.completed"


class AuditEvent(BaseModel):
    """Immutable structured audit record."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(...)
    trace_id: str = Field(...)
    parent_event_id: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str = Field(..., description="Agent or component initiating action")
    target_id: Optional[str] = Field(default=None, description="Recipient agent or resource")
    event_type: AuditEventType = Field(...)
    policy_decision: Optional[PolicyDecisionEnum] = Field(default=None)
    reason_code: Optional[str] = Field(default=None)
    policy_version: Optional[str] = Field(default="1.0.0")
    duration_ms: Optional[float] = Field(default=None)
    trust_labels: List[TrustLabel] = Field(default_factory=list)
    safe_payload_summary: Optional[str] = Field(default=None)
    payload_metadata: Dict[str, Any] = Field(default_factory=dict)
