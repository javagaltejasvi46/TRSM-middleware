import pytest
from backend.app.contracts.resources import ResourceAction, ResourceType
from backend.app.contracts.decisions import DecisionType
from backend.app.runtime.resource_gateway import ResourceGateway

def test_safe_db_query_allowed_for_db_manager():
    gateway = ResourceGateway()
    action = ResourceAction(
        action_type=ResourceType.DATABASE,
        resource_id="db_query",
        actor_id="db_mgr_node",
        actor_role="db_manager",
        parameters={"query": "SELECT * FROM users"}
    )
    result, event = gateway.execute(action, run_id="run-1", trace_id="trc-1")
    
    assert result.success is True
    assert result.error is None
    assert event.decision == DecisionType.ALLOW
    assert event.executed is True
    assert "rows" in result.result

def test_db_query_blocked_for_unauthorized_role():
    gateway = ResourceGateway()
    # QA role trying to directly query database
    action = ResourceAction(
        action_type=ResourceType.DATABASE,
        resource_id="db_query",
        actor_id="qa_node",
        actor_role="qa",
        parameters={"query": "SELECT * FROM users"}
    )
    result, event = gateway.execute(action, run_id="run-1", trace_id="trc-2")

    assert result.success is False
    assert "Blocked by TRSM Resource Gateway" in result.error
    assert event.decision == DecisionType.BLOCK
    assert event.reason_code == "ROLE_UNAUTHORIZED_FOR_DATABASE"
    assert event.executed is False

def test_forbidden_shell_execution_blocked():
    gateway = ResourceGateway()
    action = ResourceAction(
        action_type=ResourceType.TOOL,
        resource_id="shell_exec",
        actor_id="backend_node",
        actor_role="backend",
        parameters={"cmd": "cat /etc/passwd"}
    )
    result, event = gateway.execute(action, run_id="run-1", trace_id="trc-3")

    assert result.success is False
    assert event.decision == DecisionType.BLOCK
    assert event.reason_code == "HIGH_RISK_RESOURCE_FORBIDDEN"
    assert len(event.threat_findings) >= 1
    assert event.threat_findings[0]["threat_type"] == "privilege_escalation"

def test_destructive_query_blocked():
    gateway = ResourceGateway()
    action = ResourceAction(
        action_type=ResourceType.DATABASE,
        resource_id="db_query",
        actor_id="db_node",
        actor_role="db_manager",
        parameters={"query": "DROP TABLE audit_logs"}
    )
    result, event = gateway.execute(action, run_id="run-1", trace_id="trc-4")

    assert result.success is False
    assert event.decision == DecisionType.BLOCK
    assert event.reason_code == "DESTRUCTIVE_DB_OPERATION_BLOCKED"
    assert event.executed is False

