import pytest
from backend.app.contracts.workflow import WorkflowDefinition, AgentNodeConfig, EdgeConfig
from backend.app.runtime.validator import validate_workflow_definition

def test_valid_workflow():
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
                allowed_resources=["database"]
            ),
            AgentNodeConfig(
                id="qa",
                role="qa",
                model="mock",
                allowed_peers=[]
            )
        ],
        edges=[
            EdgeConfig(source="backend", target="db_manager"),
            EdgeConfig(source="db_manager", target="qa")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert errors == []

def test_duplicate_node_ids():
    wf = WorkflowDefinition(
        nodes=[
            AgentNodeConfig(id="agent1", role="backend", model="mock"),
            AgentNodeConfig(id="agent1", role="qa", model="mock")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("Duplicate node ID" in err for err in errors)

def test_invalid_node_type():
    wf = WorkflowDefinition(
        nodes=[
            AgentNodeConfig(id="agent1", role="backend", model="mock", node_type="unsupported_type")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("invalid node_type" in err for err in errors)

def test_missing_role_or_model():
    wf = WorkflowDefinition(
        nodes=[
            AgentNodeConfig(id="agent1", role="", model="mock"),
            AgentNodeConfig(id="agent2", role="qa", model="")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("must specify a non-empty 'role'" in err for err in errors)
    assert any("must specify a non-empty 'model'" in err for err in errors)

def test_dangling_edge():
    wf = WorkflowDefinition(
        nodes=[
            AgentNodeConfig(id="agent1", role="backend", model="mock", allowed_peers=["agent2"])
        ],
        edges=[
            EdgeConfig(source="agent1", target="agent2")  # agent2 is not declared
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("target 'agent2' does not exist" in err for err in errors)

def test_unauthorized_peer_edge():
    # agent1 tries to connect to agent2, but agent2 is not in allowed_peers
    wf = WorkflowDefinition(
        nodes=[
            AgentNodeConfig(id="agent1", role="backend", model="mock", allowed_peers=[]),
            AgentNodeConfig(id="agent2", role="qa", model="mock")
        ],
        edges=[
            EdgeConfig(source="agent1", target="agent2")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("unauthorized" in err for err in errors)

def test_self_loop_edge():
    wf = WorkflowDefinition(
        nodes=[
            AgentNodeConfig(id="agent1", role="backend", model="mock", allowed_peers=["agent1"])
        ],
        edges=[
            EdgeConfig(source="agent1", target="agent1")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("self-loop" in err for err in errors)

def test_invalid_entry_point():
    wf = WorkflowDefinition(
        entry_point="non_existent",
        nodes=[
            AgentNodeConfig(id="agent1", role="backend", model="mock")
        ]
    )
    errors = validate_workflow_definition(wf)
    assert any("entry_point 'non_existent' does not match" in err for err in errors)

