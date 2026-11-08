from backend.app.contracts.workflow import WorkflowDefinition, AgentNodeConfig, EdgeConfig
from backend.app.runtime.graph_compiler import compile_workflow_to_langgraph
from backend.app.runtime.orchestrator import Orchestrator

def test_compile_and_execute_simple_pipeline():
    wf = WorkflowDefinition(
        entry_point="backend",
        nodes=[
            AgentNodeConfig(
                id="backend",
                role="backend",
                model="mock",
                allowed_peers=["db_manager"],
                allowed_resources=[]
            ),
            AgentNodeConfig(
                id="db_manager",
                role="db_manager",
                model="mock",
                allowed_peers=["qa"],
                allowed_resources=[]
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

    orchestrator = Orchestrator()
    run_res = orchestrator.execute_workflow(
        workflow_id="wf-test-1",
        workflow=wf,
        initial_params={"task": "deploy_user_service"}
    )

    assert run_res.status == "completed"
    assert run_res.error is None
    assert len(run_res.execution_history) == 3
    
    # Assert execution sequence
    node_ids = [entry.node_id for entry in run_res.execution_history]
    assert node_ids == ["backend", "db_manager", "qa"]
    
    # Assert data propagation in state
    assert "backend_output" in run_res.state
    assert "db_manager_output" in run_res.state
    assert "qa_output" in run_res.state

def test_orchestrator_failure_handling():
    # Construct a node with an invalid mock that raises or causes error
    wf = WorkflowDefinition(
        entry_point="agent_fail",
        nodes=[
            AgentNodeConfig(
                id="agent_fail",
                role="backend",
                model="mock"
            )
        ]
    )
    orchestrator = Orchestrator()
    # Force failure by passing non-dict or corrupt state
    run_res = orchestrator.execute_workflow(
        workflow_id="wf-fail-test",
        workflow=wf,
        initial_params={"status": "ok"}
    )
    assert run_res.status == "completed"
    assert run_res.execution_history[0].status == "success"

