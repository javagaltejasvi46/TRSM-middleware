"""Workflow orchestrator mediating multi-agent runs."""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..schemas.events import AuditEventType
from ..schemas.messages import AgentMessageProposal
from ..schemas.policy import PolicyDecisionEnum
from ..schemas.resources import ResourceActionRequest, ResourceActionType
from ..schemas.workflow import WorkflowConfig
from ..audit.event_collector import AuditEventCollector
from .communication_gateway import AgentCommunicationGateway
from .node_guard import NodeGuard
from .resource_gateway import ControlledResourceGateway
from .adapters.mock_adapter import MockAgentAdapter


class Orchestrator:
    """Orchestrates execution of a multi-agent workflow."""

    def __init__(
        self,
        comm_gateway: Optional[AgentCommunicationGateway] = None,
        resource_gateway: Optional[ControlledResourceGateway] = None,
        event_collector: Optional[AuditEventCollector] = None,
    ):
        self.comm_gateway = comm_gateway or AgentCommunicationGateway()
        self.resource_gateway = resource_gateway or ControlledResourceGateway()
        self.event_collector = event_collector or AuditEventCollector()
        self.mock_adapter = MockAgentAdapter()

    async def run_workflow(
        self,
        workflow: WorkflowConfig,
        initial_task: str,
        enable_trsm: bool = True,
    ) -> Dict[str, Any]:
        """Execute a workflow run through mediated gateways."""
        run_id = str(uuid4())
        trace_id = str(uuid4())

        # 1. Audit event: Workflow started
        await self.event_collector.emit(
            run_id=run_id,
            trace_id=trace_id,
            actor_id="orchestrator",
            target_id=workflow.workflow_id,
            event_type=AuditEventType.WORKFLOW_STARTED,
            safe_payload_summary=f"Task: {initial_task[:80]}",
        )

        total_messages = 0
        total_tool_calls = 0
        blocked_actions = 0

        # Start with entry node
        current_node_id = workflow.entry_node_id
        current_payload = initial_task
        visited_nodes: List[str] = []

        # Find entry node configuration
        entry_node = next((n for n in workflow.nodes if n.node_id == current_node_id), None)
        if not entry_node:
            await self.event_collector.emit(
                run_id=run_id,
                trace_id=trace_id,
                actor_id="orchestrator",
                event_type=AuditEventType.WORKFLOW_FAILED,
                reason_code="ENTRY_NODE_NOT_FOUND",
            )
            return {
                "run_id": run_id,
                "workflow_id": workflow.workflow_id,
                "status": "failed",
                "enable_trsm": enable_trsm,
                "task": initial_task,
                "total_messages": 0,
                "total_tool_calls": 0,
                "blocked_actions": 1,
            }

        guard = NodeGuard(entry_node.node_id, entry_node.role.value)

        # Execution loop along configured edges (up to 5 steps for demo)
        for step in range(5):
            visited_nodes.append(current_node_id)

            # Node generates action: check if node has tools
            if entry_node.allowed_tools:
                tool_name = entry_node.allowed_tools[0]
                action_req = guard.create_resource_request(
                    resource_name=tool_name,
                    operation="read_profile" if "db" in tool_name else "read",
                    arguments={"id": "1042"},
                    action_type=ResourceActionType.DB_READ if "db" in tool_name else ResourceActionType.TOOL_CALL,
                    run_id=run_id,
                    trace_id=trace_id,
                )
                total_tool_calls += 1
                decision, res = await self.resource_gateway.mediate_action(
                    action_req, workflow=workflow, enable_trsm=enable_trsm
                )
                if decision.outcome != PolicyDecisionEnum.ALLOW:
                    blocked_actions += 1

            # Check outgoing edge
            edge = next((e for e in workflow.edges if e.source_node_id == current_node_id), None)
            if not edge:
                # Reached leaf node
                break

            target_node_id = edge.target_node_id
            proposal = guard.create_message_proposal(
                recipient_id=target_node_id,
                content=current_payload,
                run_id=run_id,
                trace_id=trace_id,
            )
            total_messages += 1

            decision, envelope = await self.comm_gateway.mediate_message(
                proposal, workflow=workflow, enable_trsm=enable_trsm
            )

            if decision.outcome != PolicyDecisionEnum.ALLOW:
                blocked_actions += 1
                # Message was blocked; receiver does not receive payload
                break

            # Move to next node
            current_node_id = target_node_id
            entry_node = next((n for n in workflow.nodes if n.node_id == current_node_id), None)
            if not entry_node:
                break
            guard = NodeGuard(entry_node.node_id, entry_node.role.value)
            current_payload = self.mock_adapter.generate_response(
                entry_node.role.value, envelope.content
            )

        # Workflow completed
        await self.event_collector.emit(
            run_id=run_id,
            trace_id=trace_id,
            actor_id="orchestrator",
            target_id=workflow.workflow_id,
            event_type=AuditEventType.WORKFLOW_COMPLETED,
        )

        return {
            "run_id": run_id,
            "workflow_id": workflow.workflow_id,
            "status": "completed",
            "enable_trsm": enable_trsm,
            "task": initial_task,
            "total_messages": total_messages,
            "total_tool_calls": total_tool_calls,
            "blocked_actions": blocked_actions,
        }
