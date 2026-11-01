def test_start_and_get_run(client):
    payload = {
        "workflow_id": "wf-1",
        "parameters": {"env": "test"}
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == "wf-1"
    assert "run_id" in data
    assert data["status"] == "pending"
    run_id = data["run_id"]

    # Test retrieval
    get_res = client.get(f"/api/runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == run_id

    # Test 404
    nf_res = client.get("/api/runs/non-existent-run")
    assert nf_res.status_code == 404

def test_start_run_validation_error(client):
    # Missing required 'workflow_id'
    response = client.post("/api/runs", json={})
    assert response.status_code == 422

