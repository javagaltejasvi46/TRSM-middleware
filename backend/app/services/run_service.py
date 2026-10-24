"""Application use-case service for workflow runs backed by SQLite persistence."""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from ..persistence.run_repository import RunRepository
from ..persistence.workflow_repository import WorkflowRepository
from ..runtime.orchestrator import Orchestrator
from ..schemas.agent import AgentNodeConfig, AgentRole
from ..schemas.workflow import WorkflowConfig, WorkflowEdge

# Global runs memory cache for instant responses
_RUNS_CACHE: Dict[str, Dict[str, Any]] = {}


class RunService:
    """Coordinates execution runs and persistence."""

    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
        run_repo: Optional[RunRepository] = None,
        workflow_repo: Optional[WorkflowRepository] = None,
    ):
        self.orchestrator = orchestrator or Orchestrator()
        self.run_repo = run_repo or RunRepository()
        self.workflow_repo = workflow_repo or WorkflowRepository()

    async def start_run(self, request) -> Dict[str, Any]:
        """Execute a workflow run and persist state across lifecycle."""
        workflow = getattr(request, "workflow", None)
        workflow_id = getattr(request, "workflow_id", None)

        if not workflow and workflow_id:
            try:
                workflow = await self.workflow_repo.get(workflow_id)
            except Exception:
                workflow = None

        if not workflow:
            # Create standard default 3-agent software engineering workflow
            backend_node = AgentNodeConfig(
                node_id="backend_agent",
                name="Backend Agent",
                role=AgentRole.BACKEND,
                allowed_peers=["db_manager_agent"],
                allowed_tools=["customer_db"],
            )
            db_node = AgentNodeConfig(
                node_id="db_manager_agent",
                name="DB Manager Agent",
                role=AgentRole.DB_MANAGER,
                allowed_peers=["qa_agent"],
                allowed_tools=["customer_db", "workflow_memory"],
            )
            qa_node = AgentNodeConfig(
                node_id="qa_agent",
                name="QA Agent",
                role=AgentRole.QA,
                allowed_peers=[],
                allowed_tools=["test_suite"],
            )
            workflow = WorkflowConfig(
                workflow_id=workflow_id or "default_se_workflow",
                name="Software Engineering 3-Agent Workflow",
                entry_node_id="backend_agent",
                nodes=[backend_node, db_node, qa_node],
                edges=[
                    WorkflowEdge(source_node_id="backend_agent", target_node_id="db_manager_agent"),
                    WorkflowEdge(source_node_id="db_manager_agent", target_node_id="qa_agent"),
                ],
            )
            try:
                await self.workflow_repo.save(workflow)
            except Exception:
                pass

        # Pre-generate run_id to persist before starting execution
        run_id = str(uuid4())
        try:
            await self.run_repo.create_run(
                run_id=run_id,
                workflow_id=workflow.workflow_id,
                status="running",
                enable_trsm=request.enable_trsm,
                task=request.task,
            )
        except Exception:
            pass

        result = await self.orchestrator.run_workflow(
            workflow=workflow,
            initial_task=request.task,
            enable_trsm=request.enable_trsm,
            run_id=run_id,
        )

        _RUNS_CACHE[result["run_id"]] = result

        # Update run in repository
        try:
            await self.run_repo.update_run(
                run_id=result["run_id"],
                status=result["status"],
                summary=result,
            )
        except Exception:
            pass

        return result

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run details from cache or SQLite."""
        if run_id in _RUNS_CACHE:
            return _RUNS_CACHE[run_id]

        try:
            record = await self.run_repo.get_run(run_id)
            if record and record.summary:
                return record.summary
            elif record:
                return {
                    "run_id": record.run_id,
                    "workflow_id": record.workflow_id,
                    "status": record.status,
                    "enable_trsm": record.enable_trsm,
                    "task": record.task,
                    "total_messages": 0,
                    "total_tool_calls": 0,
                    "blocked_actions": 0,
                }
        except Exception:
            pass
        return None

    async def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List execution runs from repository."""
        try:
            records = await self.run_repo.list_runs(limit=limit)
            if records:
                return [
                    r.summary or {
                        "run_id": r.run_id,
                        "workflow_id": r.workflow_id,
                        "status": r.status,
                        "enable_trsm": r.enable_trsm,
                        "task": r.task,
                        "total_messages": 0,
                        "total_tool_calls": 0,
                        "blocked_actions": 0,
                    }
                    for r in records
                ]
        except Exception:
            pass
        return list(_RUNS_CACHE.values())
