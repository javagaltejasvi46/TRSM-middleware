from backend.app.api.workflows import _WORKFLOWS
from backend.app.contracts.workflow import WorkflowResponse, WorkflowDefinition, AgentNodeConfig, EdgeConfig

def setup_demo_workflow():
    _WORKFLOWS.clear()
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
                allowed_peers=[],
                allowed_resources=[]
            )
        ],
        edges=[
            EdgeConfig(source="backend", target="db_manager")
        ]
    )
    _WORKFLOWS["wf-demo"] = WorkflowResponse(
        id="wf-demo",
        name="Demo 2-Agent Workflow",
        definition=wf
    )

def test_start_and_get_run_lifecycle(client):
    setup_demo_workflow()

    payload = {
        "workflow_id": "wf-demo",
        "parameters": {"environment": "staging"}
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["workflow_id"] == "wf-demo"
    assert "run_id" in data
    assert data["status"] == "completed"
    assert len(data["execution_history"]) == 2
    assert "backend_output" in data["state"]
    run_id = data["run_id"]

    # Test retrieval
    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == run_id
    assert get_res.json()["status"] == "completed"

    # Test list runs
    list_res = client.get("/api/runs")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Test 404
    nf_res = client.get("/api/runs/non-existent-run")
    assert nf_res.status_code == 404

def test_start_run_workflow_not_found(client):
    response = client.post("/api/runs", json={"workflow_id": "does-not-exist"})
    assert response.status_code == 404

def test_start_run_validation_error(client):
    # Missing required 'workflow_id'
    response = client.post("/api/runs", json={})
    assert response.status_code == 422
