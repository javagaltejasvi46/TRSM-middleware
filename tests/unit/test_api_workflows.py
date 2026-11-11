from backend.app.api.workflows import _WORKFLOWS

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_get_workflow(client):
    _WORKFLOWS.clear()
    payload = {
        "name": "Standard 3-Agent Workflow",
        "definition": {
            "entry_point": "backend",
            "nodes": [
                {
                    "id": "backend",
                    "role": "backend",
                    "model": "mock",
                    "allowed_peers": ["db_manager"],
                    "allowed_resources": []
                },
                {
                    "id": "db_manager",
                    "role": "db_manager",
                    "model": "mock",
                    "allowed_peers": ["qa"],
                    "allowed_resources": []
                },
                {
                    "id": "qa",
                    "role": "qa",
                    "model": "mock",
                    "allowed_peers": [],
                    "allowed_resources": []
                }
            ],
            "edges": [
                {"source": "backend", "target": "db_manager"},
                {"source": "db_manager", "target": "qa"}
            ]
        }
    }
    response = client.post("/api/workflows", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Standard 3-Agent Workflow"
    assert "id" in data
    wf_id = data["id"]

    # Test retrieval
    get_res = client.get(f"/api/workflows/{wf_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == wf_id

    # Test list
    list_res = client.get("/api/workflows")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Test 404 for non-existent workflow
    nf_res = client.get("/api/workflows/non-existent-wf")
    assert nf_res.status_code == 404

def test_create_workflow_validation_rejections(client):
    # Payload with invalid edge (unauthorized peer)
    invalid_payload = {
        "name": "Unauthorized Flow",
        "definition": {
            "nodes": [
                {"id": "agent_a", "role": "backend", "model": "mock", "allowed_peers": []},
                {"id": "agent_b", "role": "qa", "model": "mock", "allowed_peers": []}
            ],
            "edges": [
                {"source": "agent_a", "target": "agent_b"}
            ]
        }
    }
    response = client.post("/api/workflows", json=invalid_payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("unauthorized" in str(e) for e in data["detail"]["errors"])

def test_validate_endpoint(client):
    valid_def = {
        "nodes": [
            {"id": "node1", "role": "backend", "model": "mock", "allowed_peers": []}
        ],
        "edges": []
    }
    res = client.post("/api/workflows/validate", json=valid_def)
    assert res.status_code == 200
    assert res.json()["valid"] is True
