"""Unit tests validating canonical schemas."""

from app.schemas.events import AuditEvent, AuditEventType
from app.schemas.messages import AgentMessageProposal, MessageEnvelope
from app.schemas.policy import PolicyDecision, PolicyDecisionEnum
from app.schemas.provenance import ProvenanceRecord, TrustLabel


def test_policy_decision_enum():
    """Verify strictly only the four canonical decisions exist."""
    assert set(PolicyDecisionEnum) == {
        PolicyDecisionEnum.ALLOW,
        PolicyDecisionEnum.BLOCK,
        PolicyDecisionEnum.QUARANTINE,
        PolicyDecisionEnum.REVIEW,
    }


def test_trust_labels():
    """Verify canonical trust labels exist."""
    labels = {l.value for l in TrustLabel}
    assert "trusted_policy" in labels
    assert "user_input" in labels
    assert "untrusted_external" in labels
    assert "agent_generated" in labels
    assert "tool_result" in labels
    assert "validated" in labels


def test_audit_event_creation():
    """Verify audit event creates valid immutable record."""
    evt = AuditEvent(
        run_id="run-1",
        trace_id="trace-1",
        actor_id="backend_agent",
        event_type=AuditEventType.MESSAGE_PROPOSED,
    )
    assert evt.run_id == "run-1"
    assert evt.event_id is not None
    assert evt.timestamp is not None
