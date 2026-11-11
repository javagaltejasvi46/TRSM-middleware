from backend.app.contracts.events import AuditEvent
from backend.app.persistence.event_repository import event_repository
from backend.app.persistence.database import init_db

def test_list_and_get_events_via_api(client):
    init_db()
    test_event = AuditEvent(
        event_id="evt-api-test-1",
        run_id="run-api-1",
        trace_id="trc-api-1",
        timestamp="2026-11-11T12:00:00Z",
        event_type="GATEWAY_DECISION",
        actor_id="backend",
        target_id="db_manager",
        source_type="gateway",
        policy_decision="ALLOW",
        reason_code="POLICY_PASSED_BENIGN"
    )
    event_repository.insert_event(test_event)

    # Test list events
    response = client.get("/api/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1

    # Test filter by run_id
    filter_res = client.get("/api/events?run_id=run-api-1")
    assert filter_res.status_code == 200
    assert len(filter_res.json()) >= 1
    assert filter_res.json()[0]["run_id"] == "run-api-1"

    # Test filter non-matching run_id
    empty_res = client.get("/api/events?run_id=non-existent-run")
    assert empty_res.status_code == 200
    assert len(empty_res.json()) == 0

    # Test get event by ID
    get_res = client.get("/api/events/evt-api-test-1")
    assert get_res.status_code == 200
    assert get_res.json()["event_id"] == "evt-api-test-1"

    # Test 404
    nf_res = client.get("/api/events/non-existent-event-id")
    assert nf_res.status_code == 404
