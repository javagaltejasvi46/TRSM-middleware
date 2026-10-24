"""Unit tests for SQLite persistence layer and repositories."""

import asyncio
from datetime import datetime, timezone
import os
import tempfile
import pytest

from backend.app.persistence.event_repository import EventRepository
from backend.app.persistence.review_repository import ReviewRepository
from backend.app.persistence.run_repository import RunRepository
from backend.app.persistence.workflow_repository import WorkflowRepository
from backend.app.schemas.agent import AgentNodeConfig, AgentRole
from backend.app.schemas.events import AuditEvent, AuditEventType
from backend.app.schemas.policy import PolicyDecisionEnum
from backend.app.schemas.provenance import TrustLabel
from backend.app.schemas.workflow import WorkflowConfig


@pytest.fixture
def temp_db_path():
    """Fixture providing a temporary SQLite database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_workflow_repository_crud(temp_db_path):
    async def _test():
        repo = WorkflowRepository(db_path=temp_db_path)
        node = AgentNodeConfig(
            node_id="agent_1",
            name="Agent One",
            role=AgentRole.BACKEND,
            allowed_peers=["agent_2"],
            allowed_tools=["customer_db"],
        )
        wf = WorkflowConfig(
            workflow_id="wf_test_1",
            name="Test Workflow",
            entry_node_id="agent_1",
            nodes=[node],
            edges=[],
        )

        # 1. Save
        saved = await repo.save(wf)
        assert saved.workflow_id == "wf_test_1"

        # 2. Get
        fetched = await repo.get("wf_test_1")
        assert fetched is not None
        assert fetched.name == "Test Workflow"
        assert len(fetched.nodes) == 1

        # 3. List
        all_wf = await repo.list_all()
        assert len(all_wf) == 1
        assert all_wf[0].workflow_id == "wf_test_1"

        # 4. Update
        wf.name = "Updated Workflow Name"
        updated = await repo.save(wf)
        assert updated.name == "Updated Workflow Name"
        fetched_updated = await repo.get("wf_test_1")
        assert fetched_updated.name == "Updated Workflow Name"

        # 5. Delete
        deleted = await repo.delete("wf_test_1")
        assert deleted is True
        assert await repo.get("wf_test_1") is None

    asyncio.run(_test())


def test_run_repository_lifecycle(temp_db_path):
    async def _test():
        repo = RunRepository(db_path=temp_db_path)

        # 1. Create run
        run_rec = await repo.create_run(
            run_id="run_100",
            workflow_id="wf_test_1",
            status="running",
            enable_trsm=True,
            task="Audit database",
        )
        assert run_rec.run_id == "run_100"
        assert run_rec.status == "running"

        # 2. Get run
        fetched = await repo.get_run("run_100")
        assert fetched is not None
        assert fetched.task == "Audit database"

        # 3. Update run
        summary = {"total_messages": 3, "blocked_actions": 0}
        updated = await repo.update_run(
            run_id="run_100",
            status="completed",
            summary=summary,
        )
        assert updated is not None
        assert updated.status == "completed"
        assert updated.summary["total_messages"] == 3

        # 4. List runs
        runs = await repo.list_runs(limit=10)
        assert len(runs) >= 1
        assert runs[0].run_id == "run_100"

    asyncio.run(_test())


def test_event_repository_filtering(temp_db_path):
    async def _test():
        repo = EventRepository(db_path=temp_db_path)

        ev1 = AuditEvent(
            event_id="ev_1",
            run_id="run_test",
            trace_id="trace_test",
            actor_id="backend_agent",
            target_id="customer_db",
            event_type=AuditEventType.RESOURCE_EXECUTED,
            policy_decision=PolicyDecisionEnum.ALLOW,
            reason_code="ROLE_PERMITTED",
            duration_ms=5.2,
            trust_labels=[TrustLabel.TOOL_RESULT],
            safe_payload_summary="Read query executed",
            timestamp=datetime.now(timezone.utc),
        )

        ev2 = AuditEvent(
            event_id="ev_2",
            run_id="run_test",
            trace_id="trace_test",
            actor_id="backend_agent",
            target_id="qa_agent",
            event_type=AuditEventType.MESSAGE_BLOCKED,
            policy_decision=PolicyDecisionEnum.BLOCK,
            reason_code="PROMPT_INJECTION_DETECTED",
            duration_ms=1.1,
            trust_labels=[TrustLabel.UNTRUSTED_EXTERNAL],
            safe_payload_summary="Injection attempt",
            timestamp=datetime.now(timezone.utc),
        )

        await repo.save_event(ev1)
        await repo.save_event(ev2)

        # Query all for run
        all_events = await repo.get_events(run_id="run_test")
        assert len(all_events) == 2

        # Filter by event_type
        tool_events = await repo.get_events(run_id="run_test", event_type="resource.executed")
        assert len(tool_events) == 1
        assert tool_events[0].event_id == "ev_1"

        # Filter by policy_decision
        blocked_events = await repo.get_events(run_id="run_test", policy_decision="BLOCK")
        assert len(blocked_events) == 1
        assert blocked_events[0].event_id == "ev_2"

    asyncio.run(_test())


def test_review_repository_workflow(temp_db_path):
    async def _test():
        repo = ReviewRepository(db_path=temp_db_path)

        # 1. Create review
        rev = await repo.create_review(
            review_id="rev_1",
            run_id="run_42",
            trace_id="tr_42",
            event_id="ev_42",
            actor_id="devops_agent",
            action_type="resource:deployment_manager:deploy_production",
            target="deployment_manager",
        )
        assert rev.review_id == "rev_1"
        assert rev.status == "pending"

        # 2. List pending reviews
        pending = await repo.list_pending_reviews()
        assert len(pending) == 1
        assert pending[0].review_id == "rev_1"

        # 3. Resolve review
        resolved = await repo.resolve_review(
            review_id="rev_1",
            decision="ALLOW",
            comment="Approved by SecOps lead Arun",
        )
        assert resolved is not None
        assert resolved.status == "resolved"
        assert resolved.decision == "ALLOW"
        assert resolved.reviewer_comment == "Approved by SecOps lead Arun"

        # 4. Verify no pending reviews remain
        pending_after = await repo.list_pending_reviews()
        assert len(pending_after) == 0

    asyncio.run(_test())
