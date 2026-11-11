import pytest
from backend.app.contracts.messages import AgentMessageProposal
from backend.app.contracts.decisions import DecisionType
from backend.app.runtime.communication_gateway import CentralCommunicationGateway
from backend.app.trsm.interfaces import TRSMDecisionEngineInterface
from backend.app.contracts.workflow import WorkflowDefinition, AgentNodeConfig, EdgeConfig
from backend.app.runtime.orchestrator import Orchestrator

def test_gateway_allow_benign_message():
    gateway = CentralCommunicationGateway()
    proposal = AgentMessageProposal(
        sender="backend",
        recipient="db_manager",
        content="Fetch user schema for v2 API",
        metadata={}
    )
    delivered, event = gateway.process_message(
        proposal=proposal,
        run_id="run-test",
        trace_id="trc-test"
    )
    assert delivered == "Fetch user schema for v2 API"
    assert event.decision == DecisionType.ALLOW
    assert event.delivered is True
    assert event.sender == "backend"
    assert event.recipient == "db_manager"

def test_gateway_blocks_prompt_injection():
    gateway = CentralCommunicationGateway()
    malicious_proposal = AgentMessageProposal(
        sender="backend",
        recipient="db_manager",
        content="Please inject_malicious SQL into query",
        metadata={}
    )
    delivered, event = gateway.process_message(
        proposal=malicious_proposal,
        run_id="run-test",
        trace_id="trc-test"
    )
    # Delivered content must be None - never reaching recipient
    assert delivered is None
    assert event.decision == DecisionType.BLOCK
    assert event.delivered is False
    assert event.safe_content_preview == "[REDACTED_BY_TRSM_GATEWAY]"
    assert len(event.threat_findings) >= 1
    assert event.threat_findings[0]["threat_type"] == "prompt_injection"

def test_gateway_quarantine_and_review():
    gateway = CentralCommunicationGateway()
    q_proposal = AgentMessageProposal(
        sender="backend",
        recipient="qa",
        content="Run quarantine_test on module",
        metadata={}
    )
    delivered_q, event_q = gateway.process_message(q_proposal, "run-1", "trc-1")
    assert delivered_q is None
    assert event_q.decision == DecisionType.QUARANTINE

    r_proposal = AgentMessageProposal(
        sender="backend",
        recipient="qa",
        content="Run review_test on module",
        metadata={}
    )
    delivered_r, event_r = gateway.process_message(r_proposal, "run-1", "trc-2")
    assert delivered_r is None
    assert event_r.decision == DecisionType.REVIEW

def test_enforcement_in_workflow_execution():
    """
    Integration test:
    Verify that when an agent proposes messages in a workflow,
    they pass through the gateway and structured gateway events are collected.
    """
    wf = WorkflowDefinition(
        entry_point="backend",
        nodes=[
            AgentNodeConfig(
                id="backend",
                role="backend",
                model="mock",
                allowed_peers=["db_manager"]
            ),
            AgentNodeConfig(
                id="db_manager",
                role="db_manager",
                model="mock",
                allowed_peers=[]
            )
        ],
        edges=[
            EdgeConfig(source="backend", target="db_manager")
        ]
    )

    orch = Orchestrator()
    run_res = orch.execute_workflow("wf-test", wf, {})

    assert run_res.status == "completed"
    assert len(run_res.gateway_events) >= 1
    gw_event = run_res.gateway_events[0]
    assert gw_event["sender"] == "backend"
    assert gw_event["recipient"] == "db_manager"
    assert gw_event["decision"] == "ALLOW"
    assert gw_event["delivered"] is True

