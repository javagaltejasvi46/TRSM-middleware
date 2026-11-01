def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_and_get_workflow(client):
    # Test valid creation
    payload = {
        "name": "Test Workflow",
        "definition": {"nodes": ["backend", "db_manager"], "edges": []}
    }
    response = client.post("/api/workflows", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Workflow"
    assert "id" in data
    wf_id = data["id"]

    # Test retrieval
    get_res = client.get(f"/api/workflows/{wf_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == wf_id

    # Test 404 for non-existent workflow
    nf_res = client.get("/api/workflows/non-existent-wf")
    assert nf_res.status_code == 404

def test_create_workflow_validation_error(client):
    # Missing required 'definition' field
    payload = {"name": "Incomplete Workflow"}
    response = client.post("/api/workflows", json=payload)
    assert response.status_code == 422

