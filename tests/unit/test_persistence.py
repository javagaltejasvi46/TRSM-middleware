import os
import pytest
from backend.app.contracts.events import AuditEvent
from backend.app.persistence.database import init_db
from backend.app.persistence.event_repository import EventRepository

TEST_DB = "test_audit_events.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass
    init_db(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass

def test_insert_and_get_event():
    repo = EventRepository(TEST_DB)
    evt = AuditEvent(
        event_id="evt-test-1",
        run_id="run-1",
        trace_id="trc-1",
        parent_event_id=None,
        timestamp="2026-11-11T00:00:00Z",
        event_type="MESSAGE_PROPOSAL",
        actor_id="backend",
        target_id="db_manager",
        source_type="agent",
        trust_labels=["test"],
        policy_decision="ALLOW",
        reason_code="POLICY_PASSED_BENIGN",
        policy_version="v1.0",
        duration_ms=2.5,
        safe_payload_summary="Test summary",
        payload_reference={"detail": "sample"}
    )
    repo.insert_event(evt)
    
    retrieved = repo.get_event("evt-test-1")
    assert retrieved is not None
    assert retrieved.event_id == "evt-test-1"
    assert retrieved.actor_id == "backend"
    assert retrieved.target_id == "db_manager"
    assert retrieved.policy_decision == "ALLOW"
    assert retrieved.payload_reference == {"detail": "sample"}

def test_list_events_with_filters():
    repo = EventRepository(TEST_DB)
    evt1 = AuditEvent(
        event_id="evt-1",
        run_id="run-1",
        trace_id="trc-1",
        timestamp="2026-11-11T00:00:01Z",
        event_type="GATEWAY_DECISION",
        actor_id="backend",
        source_type="gateway",
        policy_decision="ALLOW"
    )
    evt2 = AuditEvent(
        event_id="evt-2",
        run_id="run-1",
        trace_id="trc-1",
        timestamp="2026-11-11T00:00:02Z",
        event_type="GATEWAY_DECISION",
        actor_id="backend",
        source_type="gateway",
        policy_decision="BLOCK"
    )
    evt3 = AuditEvent(
        event_id="evt-3",
        run_id="run-2",
        trace_id="trc-2",
        timestamp="2026-11-11T00:00:03Z",
        event_type="TOOL_EXECUTION",
        actor_id="db_manager",
        source_type="resource_gateway",
        policy_decision="ALLOW"
    )
    repo.insert_event(evt1)
    repo.insert_event(evt2)
    repo.insert_event(evt3)

    # Filter by run_id
    run1_events = repo.list_events(run_id="run-1")
    assert len(run1_events) == 2

    # Filter by policy_decision
    block_events = repo.list_events(policy_decision="BLOCK")
    assert len(block_events) == 1
    assert block_events[0].event_id == "evt-2"

    # Filter by actor_id
    db_events = repo.list_events(actor_id="db_manager")
    assert len(db_events) == 1
    assert db_events[0].event_id == "evt-3"
