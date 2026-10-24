"""Workflow orchestrator mediating multi-agent runs via compiled LangGraph execution."""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..audit.event_collector import AuditEventCollector
from ..schemas.events import AuditEventType
from ..schemas.workflow import WorkflowConfig
from .communication_gateway import AgentCommunicationGateway
from .graph_compiler import GraphCompiler
from .resource_gateway import ControlledResourceGateway


class Orchestrator:
    """Orchestrates execution of a multi-agent workflow using LangGraph state machines."""

    def __init__(
        self,
        comm_gateway: Optional[AgentCommunicationGateway] = None,
        resource_gateway: Optional[ControlledResourceGateway] = None,
        event_collector: Optional[AuditEventCollector] = None,
        graph_compiler: Optional[GraphCompiler] = None,
    ):
        self.comm_gateway = comm_gateway or AgentCommunicationGateway()
        self.resource_gateway = resource_gateway or ControlledResourceGateway()
        self.event_collector = event_collector or AuditEventCollector()
        self.graph_compiler = graph_compiler or GraphCompiler(
            comm_gateway=self.comm_gateway,
            resource_gateway=self.resource_gateway,
            event_collector=self.event_collector,
        )

    async def run_workflow(
        self,
        workflow: WorkflowConfig,
        initial_task: str,
        enable_trsm: bool = True,
        run_id: Optional[str] = None,
        use_ollama: bool = False,
    ) -> Dict[str, Any]:
        """Execute a workflow run through mediated LangGraph execution."""
        active_run_id = run_id or str(uuid4())
        trace_id = str(uuid4())

        # 1. Audit event: Workflow started
        await self.event_collector.emit(
            run_id=active_run_id,
            trace_id=trace_id,
            actor_id="orchestrator",
            target_id=workflow.workflow_id,
            event_type=AuditEventType.WORKFLOW_STARTED,
            safe_payload_summary=f"Task: {initial_task[:80]}",
        )

        # 2. Check entry node existence
        entry_node = next((n for n in workflow.nodes if n.node_id == workflow.entry_node_id), None)
        if not entry_node:
            await self.event_collector.emit(
                run_id=active_run_id,
                trace_id=trace_id,
                actor_id="orchestrator",
                event_type=AuditEventType.WORKFLOW_FAILED,
                reason_code="ENTRY_NODE_NOT_FOUND",
            )
            return {
                "run_id": active_run_id,
                "workflow_id": workflow.workflow_id,
                "status": "failed",
                "enable_trsm": enable_trsm,
                "task": initial_task,
                "total_messages": 0,
                "total_tool_calls": 0,
                "blocked_actions": 1,
            }

        # 3. Compile and execute LangGraph
        try:
            compiled_graph = self.graph_compiler.compile(
                workflow=workflow,
                enable_trsm=enable_trsm,
                use_ollama=use_ollama,
            )

            initial_state = {
                "run_id": active_run_id,
                "trace_id": trace_id,
                "current_node_id": workflow.entry_node_id,
                "payload": initial_task,
                "visited_nodes": [],
                "step_count": 0,
                "total_messages": 0,
                "total_tool_calls": 0,
                "blocked_actions": 0,
                "status": "running",
                "workflow_id": workflow.workflow_id,
                "enable_trsm": enable_trsm,
            }

            final_state = await compiled_graph.ainvoke(initial_state)

            final_status = "blocked" if final_state.get("status") == "blocked" else "completed"
            total_msgs = final_state.get("total_messages", 0)
            total_tools = final_state.get("total_tool_calls", 0)
            blocked_acts = final_state.get("blocked_actions", 0)

            # Audit event: Workflow completed
            await self.event_collector.emit(
                run_id=active_run_id,
                trace_id=trace_id,
                actor_id="orchestrator",
                target_id=workflow.workflow_id,
                event_type=AuditEventType.WORKFLOW_COMPLETED if final_status == "completed" else AuditEventType.WORKFLOW_FAILED,
                reason_code=None if final_status == "completed" else "POLICY_BLOCKED",
            )

            return {
                "run_id": active_run_id,
                "workflow_id": workflow.workflow_id,
                "status": final_status,
                "enable_trsm": enable_trsm,
                "task": initial_task,
                "total_messages": total_msgs,
                "total_tool_calls": total_tools,
                "blocked_actions": blocked_acts,
                "visited_nodes": final_state.get("visited_nodes", []),
            }

        except Exception as exc:
            await self.event_collector.emit(
                run_id=active_run_id,
                trace_id=trace_id,
                actor_id="orchestrator",
                target_id=workflow.workflow_id,
                event_type=AuditEventType.WORKFLOW_FAILED,
                reason_code=str(exc)[:80],
            )
            return {
                "run_id": active_run_id,
                "workflow_id": workflow.workflow_id,
                "status": "failed",
                "enable_trsm": enable_trsm,
                "task": initial_task,
                "total_messages": 0,
                "total_tool_calls": 0,
                "blocked_actions": 1,
                "error": str(exc),
            }
