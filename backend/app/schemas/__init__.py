"""Canonical Pydantic contracts for TRSM."""

from .agent import AgentNodeConfig, AgentRole, AgentStatus
from .events import AuditEvent, AuditEventType
from .messages import AgentMessageProposal, MessageEnvelope
from .metrics import MetricResult, RunMetrics
from .policy import PolicyDecision, PolicyDecisionEnum
from .provenance import ProvenanceRecord, TrustLabel
from .resources import ResourceActionRequest, ResourceActionResult
from .threats import ThreatFamily, ThreatFinding, ThreatSeverity
from .workflow import WorkflowConfig, WorkflowEdge, WorkflowValidationResult

__all__ = [
    "AgentNodeConfig",
    "AgentRole",
    "AgentStatus",
    "AuditEvent",
    "AuditEventType",
    "AgentMessageProposal",
    "MessageEnvelope",
    "MetricResult",
    "RunMetrics",
    "PolicyDecision",
    "PolicyDecisionEnum",
    "ProvenanceRecord",
    "TrustLabel",
    "ResourceActionRequest",
    "ResourceActionResult",
    "ThreatFamily",
    "ThreatFinding",
    "ThreatSeverity",
    "WorkflowConfig",
    "WorkflowEdge",
    "WorkflowValidationResult",
]
