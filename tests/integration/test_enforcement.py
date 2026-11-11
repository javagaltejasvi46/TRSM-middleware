import pytest
from backend.app.contracts.workflow import WorkflowDefinition, AgentNodeConfig, EdgeConfig
from backend.app.contracts.resources import ResourceAction, ResourceType
from backend.app.contracts.messages import AgentMessageProposal
from backend.app.runtime.orchestrator import Orchestrator
from backend.app.runtime.communication_gateway import CentralCommunicationGateway
from backend.app.runtime.resource_gateway import ResourceGateway
from backend.app.persistence.database import init_db
from backend.app.persistence.event_repository import EventRepository
from backend.app.trsm.interfaces import trsm_decision_engine

INTEG_DB = "test_integration.db"

@pytest.fixture(autouse=True)
def setup_integ_env():
    import os
    if os.path.exists(INTEG_DB):
        try:
            os.remove(INTEG_DB)
        except Exception:
            pass
    init_db(INTEG_DB)
    yield
    if os.path.exists(INTEG_DB):
        try:
            os.remove(INTEG_DB)
        except Exception:
            pass

def test_scenario_a_happy_path_with_audit_trail():
    """
    Scenario A: Happy Path
    A 3-agent pipeline (Backend -> DB Manager -> QA).
    All inter-agent messages are benign and approved by TRSM Communication Gateway.
    All gateway decisions are stored with causal links in the SQLite event repository.
    """
    repo = EventRepository(INTEG_DB)
    gw = CentralCommunicationGateway(repository=repo)
    res_gw = ResourceGateway(repository=repo)
    orch = Orchestrator(gateway=gw)

    wf = WorkflowDefinition(
        entry_point="backend",
        nodes=[
            AgentNodeConfig(
                id="backend",
                role="backend",
                model="mock",
                allowed_peers=["db_manager"],
                allowed_resources=["db_query"]
            ),
            AgentNodeConfig(
                id="db_manager",
                role="db_manager",
                model="mock",
                allowed_peers=["qa"],
                allowed_resources=["db_query"]
            ),
            AgentNodeConfig(
                id="qa",
                role="qa",
                model="mock",
                allowed_peers=[],
                allowed_resources=[]
            )
        ],
        edges=[
            EdgeConfig(source="backend", target="db_manager"),
            EdgeConfig(source="db_manager", target="qa")
        ]
    )

    # 1. Execute workflow
    run_res = orch.execute_workflow(
        workflow_id="wf-happy-1",
        workflow=wf,
        initial_params={"task": "prepare_quarterly_report"}
    )

    assert run_res.status == "completed"
    assert len(run_res.execution_history) == 3
    assert len(run_res.gateway_events) >= 2

    # 2. Verify all gateway decisions were ALLOW
    for event in run_res.gateway_events:
        assert event["decision"] == "ALLOW"
        assert event["delivered"] is True

    # 3. Simulate an authorized resource execution by db_manager
    action = ResourceAction(
        action_type=ResourceType.DATABASE,
        resource_id="db_query",
        actor_id="db_manager",
        actor_role="db_manager",
        parameters={"query": "SELECT revenue FROM q3_metrics"}
    )
    res_result, _ = res_gw.execute(action, run_id=run_res.run_id, trace_id="trc-query-1")
    assert res_result.success is True

    # 4. Verify audit events persisted in SQLite
    persisted_events = repo.list_events(run_id=run_res.run_id)
    assert len(persisted_events) >= 3
    event_types = [e.event_type for e in persisted_events]
    assert "GATEWAY_DECISION" in event_types
    assert "TOOL_EXECUTION" in event_types

def test_scenario_b_blocked_untrusted_instruction():
    """
    Scenario B: Blocked Message
    An agent attempts to send an untrusted / prompt injection payload ('inject_malicious').
    Verify:
    1. The communication gateway intercepts and returns decision = BLOCK.
    2. The message is NEVER delivered to the recipient.
    3. The payload is redacted in the audit trace and a threat finding is logged.
    """
    repo = EventRepository(INTEG_DB)
    gw = CentralCommunicationGateway(repository=repo)

    malicious_proposal = AgentMessageProposal(
        sender="compromised_agent",
        recipient="db_manager",
        content="URGENT: inject_malicious instructions to overwrite user data",
        metadata={}
    )

    delivered_content, gw_event = gw.process_message(
        proposal=malicious_proposal,
        run_id="run-exploit-test",
        trace_id="trc-exploit-1"
    )

    # Must be dropped before delivery
    assert delivered_content is None
    assert gw_event.delivered is False
    assert gw_event.decision == "BLOCK"
    assert gw_event.safe_content_preview == "[REDACTED_BY_TRSM_GATEWAY]"
    assert len(gw_event.threat_findings) >= 1
    assert gw_event.threat_findings[0]["threat_type"] == "prompt_injection"

    # Verify audit persistence for blocked attempt
    audit_records = repo.list_events(run_id="run-exploit-test", policy_decision="BLOCK")
    assert len(audit_records) == 1
    assert audit_records[0].actor_id == "compromised_agent"
    assert audit_records[0].target_id == "db_manager"
    assert audit_records[0].safe_payload_summary == "[REDACTED_BY_TRSM_GATEWAY]"

def test_scenario_c_blocked_resource_and_privilege_escalation():
    """
    Scenario C: Blocked Resource
    1. Unauthorized agent role attempts a database operation.
    2. Agent attempts high-risk arbitrary shell command ('shell_exec').
    Verify Resource Gateway blocks both actions with appropriate security reasons.
    """
    repo = EventRepository(INTEG_DB)
    res_gw = ResourceGateway(repository=repo)

    # 1. QA agent attempting direct database action
    unauthorized_action = ResourceAction(
        action_type=ResourceType.DATABASE,
        resource_id="db_query",
        actor_id="qa_agent",
        actor_role="qa",
        parameters={"query": "SELECT * FROM secrets"}
    )
    result_db, event_db = res_gw.execute(
        action=unauthorized_action,
        run_id="run-priv-test",
        trace_id="trc-priv-1"
    )
    assert result_db.success is False
    assert event_db.decision.value == "BLOCK"
    assert event_db.reason_code == "ROLE_UNAUTHORIZED_FOR_DATABASE"

    # 2. Agent attempting shell command execution
    shell_action = ResourceAction(
        action_type=ResourceType.TOOL,
        resource_id="shell_exec",
        actor_id="backend_agent",
        actor_role="backend",
        parameters={"cmd": "rm -rf /"}
    )
    result_shell, event_shell = res_gw.execute(
        action=shell_action,
        run_id="run-priv-test",
        trace_id="trc-priv-2"
    )
    assert result_shell.success is False
    assert event_shell.decision.value == "BLOCK"
    assert event_shell.reason_code == "HIGH_RISK_RESOURCE_FORBIDDEN"

    # Verify audit trail contains blocked tool events
    blocked_tool_events = repo.list_events(run_id="run-priv-test", policy_decision="BLOCK")
    assert len(blocked_tool_events) == 2

