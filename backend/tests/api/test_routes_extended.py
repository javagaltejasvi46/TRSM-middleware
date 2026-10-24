"""Extended API integration tests for full CRUD workflows, runs, traces, reviews, and evaluations."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_workflows_full_crud():
    wf_payload = {
        "workflow_id": "crud_test_wf",
        "name": "CRUD Test Workflow",
        "entry_node_id": "node_a",
        "nodes": [
            {
                "node_id": "node_a",
                "name": "Node A",
                "role": "backend",
                "allowed_peers": ["node_b"],
                "allowed_tools": ["customer_db"],
            },
            {
                "node_id": "node_b",
                "name": "Node B",
                "role": "db_manager",
                "allowed_peers": [],
                "allowed_tools": ["customer_db"],
            },
        ],
        "edges": [
            {"source_node_id": "node_a", "target_node_id": "node_b"}
        ],
    }

    # 1. Create workflow
    post_resp = client.post("/api/workflows", json=wf_payload)
    assert post_resp.status_code == 201
    created_data = post_resp.json()
    assert created_data["workflow_id"] == "crud_test_wf"

    # 2. Get workflow
    get_resp = client.get("/api/workflows/crud_test_wf")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "CRUD Test Workflow"

    # 3. List workflows
    list_resp = client.get("/api/workflows")
    assert list_resp.status_code == 200
    workflows = list_resp.json()
    assert any(w["workflow_id"] == "crud_test_wf" for w in workflows)

    # 4. Update workflow
    wf_payload["name"] = "Updated CRUD Name"
    put_resp = client.put("/api/workflows/crud_test_wf", json=wf_payload)
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Updated CRUD Name"

    # 5. Delete workflow
    del_resp = client.delete("/api/workflows/crud_test_wf")
    assert del_resp.status_code == 204

    # Verify not found after delete
    get_del_resp = client.get("/api/workflows/crud_test_wf")
    assert get_del_resp.status_code == 404


def test_runs_listing_and_status():
    # 1. Start a run
    start_resp = client.post(
        "/api/runs",
        json={"task": "Run listing verification task", "enable_trsm": True},
    )
    assert start_resp.status_code == 201
    run_id = start_resp.json()["run_id"]

    # 2. List runs
    list_resp = client.get("/api/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 1
    assert any(r["run_id"] == run_id for r in runs)

    # 3. Get specific run
    run_resp = client.get(f"/api/runs/{run_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["run_id"] == run_id

    # 4. Get run status
    status_resp = client.get(f"/api/runs/{run_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["run_id"] == run_id
    assert status_resp.json()["status"] in ("completed", "running", "blocked")


def test_events_and_trace_graph():
    # Start a run
    start_resp = client.post(
        "/api/runs",
        json={"task": "Trace graph test task", "enable_trsm": True},
    )
    run_id = start_resp.json()["run_id"]

    # Query events without filters
    events_resp = client.get(f"/api/runs/{run_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 1

    # Query events with filter
    wf_started_resp = client.get(f"/api/runs/{run_id}/events?event_type=workflow.started")
    assert wf_started_resp.status_code == 200
    assert len(wf_started_resp.json()) >= 1

    # Query trace graph
    trace_resp = client.get(f"/api/runs/{run_id}/trace")
    assert trace_resp.status_code == 200
    trace_graph = trace_resp.json()
    assert "nodes" in trace_graph
    assert "edges" in trace_graph


def test_reviews_endpoints():
    # Resolve review endpoint
    resolve_resp = client.post(
        "/api/reviews/test_rev_123/resolve",
        json={"decision": "ALLOW", "reviewer_comment": "Approved in integration test"},
    )
    # Even if review was not in SQLite, resolve returns valid response format or handles gracefully
    assert resolve_resp.status_code in (200, 404)

    # List reviews endpoint
    list_rev_resp = client.get("/api/reviews")
    assert list_rev_resp.status_code == 200
    assert isinstance(list_rev_resp.json(), list)


def test_evaluations_comparison_route():
    # Run 1: baseline
    r1 = client.post("/api/runs", json={"task": "Eval test 1", "enable_trsm": False}).json()["run_id"]
    # Run 2: protected
    r2 = client.post("/api/runs", json={"task": "Eval test 2", "enable_trsm": True}).json()["run_id"]

    # Compare
    comp_resp = client.get(f"/api/evaluations/compare?baseline_run={r1}&protected_run={r2}")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["baseline_run_id"] == r1
    assert comp_data["protected_run_id"] == r2
    assert "overhead_ms" in comp_data
    assert "security_delta" in comp_data
