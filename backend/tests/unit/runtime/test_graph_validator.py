"""Unit tests for server-side graph validation."""

from backend.app.runtime.graph_validator import GraphValidator
from backend.app.schemas.agent import AgentNodeConfig, AgentRole
from backend.app.schemas.workflow import WorkflowConfig, WorkflowEdge


def test_graph_validator_valid_workflow():
    node1 = AgentNodeConfig(
        node_id="backend",
        name="Backend",
        role=AgentRole.BACKEND,
        allowed_peers=["db"],
    )
    node2 = AgentNodeConfig(
        node_id="db",
        name="DB",
        role=AgentRole.DB_MANAGER,
        allowed_peers=[],
    )
    wf = WorkflowConfig(
        workflow_id="wf_valid",
        name="Valid Workflow",
        entry_node_id="backend",
        nodes=[node1, node2],
        edges=[WorkflowEdge(source_node_id="backend", target_node_id="db")],
    )
    validator = GraphValidator()
    res = validator.validate(wf)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_graph_validator_duplicate_nodes():
    node1 = AgentNodeConfig(node_id="backend", name="Backend 1", role=AgentRole.BACKEND)
    node2 = AgentNodeConfig(node_id="backend", name="Backend 2", role=AgentRole.BACKEND)
    wf = WorkflowConfig(
        workflow_id="wf_dup",
        name="Dup Workflow",
        entry_node_id="backend",
        nodes=[node1, node2],
        edges=[],
    )
    validator = GraphValidator()
    res = validator.validate(wf)
    assert res.is_valid is False
    assert any("Duplicate node ID" in err for err in res.errors)


def test_graph_validator_self_loop_detected():
    node1 = AgentNodeConfig(
        node_id="backend",
        name="Backend",
        role=AgentRole.BACKEND,
        allowed_peers=["backend"],
    )
    wf = WorkflowConfig(
        workflow_id="wf_loop",
        name="Loop Workflow",
        entry_node_id="backend",
        nodes=[node1],
        edges=[WorkflowEdge(source_node_id="backend", target_node_id="backend")],
    )
    validator = GraphValidator()
    res = validator.validate(wf)
    assert res.is_valid is False
    assert any("Self-loop detected" in err for err in res.errors)


def test_graph_validator_missing_entry_node():
    node1 = AgentNodeConfig(node_id="backend", name="Backend", role=AgentRole.BACKEND)
    wf = WorkflowConfig(
        workflow_id="wf_missing",
        name="Missing Entry",
        entry_node_id="nonexistent_entry",
        nodes=[node1],
        edges=[],
    )
    validator = GraphValidator()
    res = validator.validate(wf)
    assert res.is_valid is False
    assert any("Entry node" in err for err in res.errors)


def test_graph_validator_warns_on_unlisted_peer_edge():
    node1 = AgentNodeConfig(node_id="backend", name="Backend", role=AgentRole.BACKEND, allowed_peers=[])
    node2 = AgentNodeConfig(node_id="db", name="DB", role=AgentRole.DB_MANAGER, allowed_peers=[])
    wf = WorkflowConfig(
        workflow_id="wf_warn",
        name="Warn Workflow",
        entry_node_id="backend",
        nodes=[node1, node2],
        edges=[WorkflowEdge(source_node_id="backend", target_node_id="db")],
    )
    validator = GraphValidator()
    res = validator.validate(wf)
    # Warnings exist for security discrepancy
    assert len(res.warnings) > 0
    assert any("not in source node's allowed_peers list" in w for w in res.warnings)
