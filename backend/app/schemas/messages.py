"""Inter-agent message proposals and delivery envelopes."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from .provenance import ProvenanceRecord, TrustLabel


class MessageDeliveryStatus(str, Enum):
    """Delivery status of an inter-agent message."""
    PROPOSED = "proposed"
    DELIVERED = "delivered"
    BLOCKED = "blocked"
    QUARANTINED = "quarantined"
    AWAITING_REVIEW = "awaiting_review"


class AgentMessageProposal(BaseModel):
    """Message proposed by an agent, submitted to the Communication Gateway."""
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(..., description="Active workflow run ID")
    trace_id: str = Field(..., description="Correlation trace scope")
    sender_id: str = Field(..., description="Registered identity of sending node")
    recipient_id: str = Field(..., description="Intended recipient node ID")
    content: str = Field(..., description="Message payload")
    provenance: Optional[ProvenanceRecord] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageEnvelope(BaseModel):
    """Immutable envelope delivered to the receiving agent upon authorization."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_id: str = Field(..., description="Underlying proposal ID")
    run_id: str = Field(...)
    trace_id: str = Field(...)
    sender_id: str = Field(...)
    recipient_id: str = Field(...)
    content: str = Field(...)
    provenance: ProvenanceRecord = Field(...)
    status: MessageDeliveryStatus = Field(default=MessageDeliveryStatus.DELIVERED)
    policy_decision_id: str = Field(..., description="ID of authoritative ALLOW decision")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
