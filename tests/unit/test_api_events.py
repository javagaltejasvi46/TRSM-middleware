from backend.app.api.events import _EVENTS, Event

def test_list_and_get_events(client):
    # Seed an event for testing
    _EVENTS.clear()
    test_event = Event(
        event_id="evt-100",
        run_id="run-1",
        event_type="MESSAGE_PROPOSAL",
        timestamp="2026-11-01T12:00:00Z",
        payload={"message": "hello"}
    )
    _EVENTS.append(test_event)

    # Test list all events
    response = client.get("/api/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_id"] == "evt-100"

    # Test filter by run_id
    filter_res = client.get("/api/events?run_id=run-1")
    assert filter_res.status_code == 200
    assert len(filter_res.json()) == 1

    empty_filter = client.get("/api/events?run_id=non-existent-run")
    assert empty_filter.status_code == 200
    assert len(empty_filter.json()) == 0

    # Test get event by ID
    get_res = client.get("/api/events/evt-100")
    assert get_res.status_code == 200
    assert get_res.json()["event_id"] == "evt-100"

    # Test 404
    nf_res = client.get("/api/events/non-existent-event")
    assert nf_res.status_code == 404

