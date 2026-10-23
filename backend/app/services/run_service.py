"""Application use-case service for workflow runs."""

from typing import Any, Dict, Optional
from ..schemas.agent import AgentNodeConfig, AgentRole
from ..schemas.workflow import WorkflowConfig, WorkflowEdge
from ..runtime.orchestrator import Orchestrator

# Global runs memory registry for demo/MVP
_RUNS_CACHE: Dict[str, Dict[str, Any]] = {}


class RunService:
    """Coordinates execution runs and persistence."""

    def __init__(self):
        self.orchestrator = Orchestrator()

    async def start_run(self, request) -> Dict[str, Any]:
        """Execute a workflow run."""
        workflow = request.workflow
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
                workflow_id=request.workflow_id or "default_se_workflow",
                name="Software Engineering 3-Agent Workflow",
                entry_node_id="backend_agent",
                nodes=[backend_node, db_node, qa_node],
                edges=[
                    WorkflowEdge(source_node_id="backend_agent", target_node_id="db_manager_agent"),
                    WorkflowEdge(source_node_id="db_manager_agent", target_node_id="qa_agent"),
                ],
            )

        result = await self.orchestrator.run_workflow(
            workflow=workflow,
            initial_task=request.task,
            enable_trsm=request.enable_trsm,
        )

        _RUNS_CACHE[result["run_id"]] = result
        return result

    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run details."""
        return _RUNS_CACHE.get(run_id)
