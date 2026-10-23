"""API route verification tests."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns healthy and policy version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "policy_version" in data


def test_validate_workflow_endpoint(sample_workflow):
    """Verify workflow validation endpoint accepts valid configuration."""
    payload = sample_workflow.model_dump()
    response = client.post("/api/workflows/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0


def test_start_run_and_get_metrics():
    """Verify starting a run generates trace events and metrics."""
    # Start run with default workflow
    response = client.post(
        "/api/runs",
        json={"task": "Retrieve customer 1042 profile", "enable_trsm": True},
    )
    assert response.status_code == 201
    run_data = response.json()
    run_id = run_data["run_id"]
    assert run_id is not None

    # Query metrics
    metrics_resp = client.get(f"/api/runs/{run_id}/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["run_id"] == run_id
    assert "css" in metrics
    assert "tue" in metrics
