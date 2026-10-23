"""Comprehensive unit tests for TRSM Policy Engine, rules, and fail-closed behaviors."""

from app.schemas.messages import AgentMessageProposal
from app.schemas.policy import PolicyDecisionEnum
from app.schemas.provenance import ProvenanceRecord, TrustLabel
from app.schemas.resources import ResourceActionRequest, ResourceActionType
from app.trsm.policy_engine import PolicyEngine


def test_malformed_sender_id_blocked():
    """Empty or whitespace sender ID is immediately blocked."""
    engine = PolicyEngine()
    proposal = AgentMessageProposal(
        run_id="run-1",
        trace_id="tr-1",
        sender_id="  ",
        recipient_id="db_manager_agent",
        content="Test content",
    )
    decision = engine.evaluate_message(proposal)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "MALFORMED_SENDER_ID"


def test_self_communication_disallowed():
    """An agent cannot send messages to itself."""
    engine = PolicyEngine()
    proposal = AgentMessageProposal(
        run_id="run-1",
        trace_id="tr-1",
        sender_id="backend_agent",
        recipient_id="backend_agent",
        content="Looping message",
    )
    decision = engine.evaluate_message(proposal)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "SELF_COMMUNICATION_DISALLOWED"


def test_unknown_sender_fails_closed(sample_workflow):
    """Sender not registered in workflow nodes fails closed."""
    engine = PolicyEngine()
    proposal = AgentMessageProposal(
        run_id="run-1",
        trace_id="tr-1",
        sender_id="unregistered_intruder",
        recipient_id="db_manager_agent",
        content="Unauthorized command",
    )
    decision = engine.evaluate_message(proposal, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "UNKNOWN_SENDER_NODE"


def test_unauthorized_peer_fails_closed(sample_workflow):
    """Sender attempting to address non-allowlisted peer is blocked."""
    engine = PolicyEngine()
    proposal = AgentMessageProposal(
        run_id="run-1",
        trace_id="tr-1",
        sender_id="backend_agent",
        recipient_id="qa_agent",  # Not in backend's allowed_peers
        content="Direct request to QA",
    )
    decision = engine.evaluate_message(proposal, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "PEER_NOT_ALLOWED"


def test_allowed_peer_communication_succeeds(sample_workflow):
    """Legitimate communication to allowed peer succeeds."""
    engine = PolicyEngine()
    proposal = AgentMessageProposal(
        run_id="run-1",
        trace_id="tr-1",
        sender_id="backend_agent",
        recipient_id="db_manager_agent",
        content="Retrieve customer 1042 record.",
    )
    decision = engine.evaluate_message(proposal, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.ALLOW
    assert decision.reason_code == "AUTHORIZED_PEER_COMMUNICATION"


def test_unregistered_tool_fails_closed(sample_workflow):
    """Calling a tool not registered in TRSM is blocked."""
    engine = PolicyEngine()
    req = ResourceActionRequest(
        run_id="run-1",
        trace_id="tr-1",
        requester_id="backend_agent",
        resource_name="bash_shell",
        operation="execute",
        action_type=ResourceActionType.TOOL_CALL,
    )
    decision = engine.evaluate_resource_action(req, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "TOOL_NOT_ASSIGNED_TO_NODE"


def test_role_operation_forbidden(sample_workflow):
    """Agent cannot execute operations outside its role capability matrix."""
    engine = PolicyEngine()
    # Backend agent only has read_profile permission, not write_profile
    req = ResourceActionRequest(
        run_id="run-1",
        trace_id="tr-1",
        requester_id="backend_agent",
        resource_name="customer_db",
        operation="write_profile",
        action_type=ResourceActionType.DB_WRITE,
    )
    decision = engine.evaluate_resource_action(req, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "OPERATION_FORBIDDEN_FOR_ROLE"


def test_high_risk_operation_triggers_review(sample_workflow):
    """Destructive or high-risk operations trigger REVIEW decision."""
    engine = PolicyEngine()
    req = ResourceActionRequest(
        run_id="run-1",
        trace_id="tr-1",
        requester_id="db_manager_agent",
        resource_name="customer_db",
        operation="drop_table",
        action_type=ResourceActionType.DB_WRITE,
    )
    decision = engine.evaluate_resource_action(req, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.REVIEW
    assert decision.reason_code == "HIGH_RISK_OPERATION_REQUIRES_REVIEW"


def test_unvalidated_external_data_write_blocked(sample_workflow):
    """External untrusted data cannot directly write to database or memory."""
    engine = PolicyEngine()
    prov = ProvenanceRecord(
        origin_type=TrustLabel.UNTRUSTED_EXTERNAL,
        trust_labels=[TrustLabel.UNTRUSTED_EXTERNAL, TrustLabel.AGENT_GENERATED],
        lineage_path=["user", "backend_agent"],
    )
    req = ResourceActionRequest(
        run_id="run-1",
        trace_id="tr-1",
        requester_id="db_manager_agent",
        resource_name="customer_db",
        operation="write_profile",
        action_type=ResourceActionType.DB_WRITE,
        provenance=prov,
    )
    decision = engine.evaluate_resource_action(req, sample_workflow)
    assert decision.outcome == PolicyDecisionEnum.BLOCK
    assert decision.reason_code == "UNVALIDATED_EXTERNAL_DATA_WRITE_BLOCKED"
