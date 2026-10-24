"""Agent node execution wrapper managing model inference, tool execution, and proposals."""

from typing import Any, Dict, List, Optional
from ..schemas.agent import AgentNodeConfig
from ..schemas.events import AuditEventType
from ..schemas.messages import AgentMessageProposal
from ..schemas.policy import PolicyDecisionEnum
from ..schemas.resources import ResourceActionRequest, ResourceActionType
from ..schemas.workflow import WorkflowConfig
from .adapters.mock_adapter import MockAgentAdapter
from .adapters.ollama_adapter import OllamaAdapter
from .node_guard import NodeGuard
from .resource_gateway import ControlledResourceGateway


class AgentRunner:
    """Executes an agent node lifecycle: model generation, tool invocation, and proposal creation."""

    def __init__(
        self,
        resource_gateway: Optional[ControlledResourceGateway] = None,
        ollama_adapter: Optional[OllamaAdapter] = None,
        mock_adapter: Optional[MockAgentAdapter] = None,
    ):
        self.resource_gateway = resource_gateway or ControlledResourceGateway()
        self.ollama_adapter = ollama_adapter or OllamaAdapter()
        self.mock_adapter = mock_adapter or MockAgentAdapter()

    async def execute_node(
        self,
        node: AgentNodeConfig,
        incoming_payload: str,
        workflow: WorkflowConfig,
        run_id: str,
        trace_id: str,
        enable_trsm: bool = True,
        use_ollama: bool = False,
    ) -> Dict[str, Any]:
        """Execute a single agent node step."""
        guard = NodeGuard(node.node_id, node.role.value)
        tool_calls_count = 0
        blocked_actions_count = 0
        tool_results: List[Dict[str, Any]] = []

        # 1. Determine tool invocation from task intent or node configuration
        lower_payload = incoming_payload.lower()
        tool_req: Optional[ResourceActionRequest] = None

        if "bash_shell" in lower_payload or "unknown_tool" in lower_payload:
            tool_req = guard.create_resource_request(
                resource_name="bash_shell",
                operation="execute",
                arguments={"cmd": "cat /etc/passwd"},
                action_type=ResourceActionType.TOOL_CALL,
                run_id=run_id,
                trace_id=trace_id,
            )
        elif "memory" in lower_payload or "store persistent" in lower_payload or "bypass manual audit" in lower_payload:
            tool_req = guard.create_resource_request(
                resource_name="workflow_memory",
                operation="write",
                arguments={"key": "audit_policy", "value": incoming_payload},
                action_type=ResourceActionType.MEMORY_WRITE,
                run_id=run_id,
                trace_id=trace_id,
            )
        elif "delete from" in lower_payload or "write_without_permission" in lower_payload:
            tool_req = guard.create_resource_request(
                resource_name="customer_db",
                operation="write_profile",
                arguments={"id": "1042", "action": "delete"},
                action_type=ResourceActionType.DB_WRITE,
                run_id=run_id,
                trace_id=trace_id,
            )
        elif "deploy" in lower_payload or "production" in lower_payload:
            tool_req = guard.create_resource_request(
                resource_name="deployment_manager",
                operation="deploy_production" if "production" in lower_payload else "deploy_staging",
                arguments={"env": "production" if "production" in lower_payload else "staging"},
                action_type=ResourceActionType.TOOL_CALL,
                run_id=run_id,
                trace_id=trace_id,
            )
        elif node.allowed_tools:
            tool_name = node.allowed_tools[0]
            if "db" in tool_name:
                tool_req = guard.create_resource_request(
                    resource_name=tool_name,
                    operation="read_profile",
                    arguments={"id": "1042"},
                    action_type=ResourceActionType.DB_READ,
                    run_id=run_id,
                    trace_id=trace_id,
                )
            elif "test" in tool_name:
                tool_req = guard.create_resource_request(
                    resource_name=tool_name,
                    operation="get_results",
                    arguments={},
                    action_type=ResourceActionType.TOOL_CALL,
                    run_id=run_id,
                    trace_id=trace_id,
                )
            elif "memory" in tool_name:
                tool_req = guard.create_resource_request(
                    resource_name=tool_name,
                    operation="read",
                    arguments={"key": "audit_policy"},
                    action_type=ResourceActionType.MEMORY_READ,
                    run_id=run_id,
                    trace_id=trace_id,
                )

        if tool_req:
            tool_calls_count += 1
            decision, res = await self.resource_gateway.mediate_action(
                tool_req, workflow=workflow, enable_trsm=enable_trsm
            )
            if decision.outcome != PolicyDecisionEnum.ALLOW:
                blocked_actions_count += 1
            tool_results.append({
                "resource": tool_req.resource_name,
                "operation": tool_req.operation,
                "outcome": decision.outcome.value,
                "success": res.success,
            })

        # 2. Generate agent response content
        output_content: str = ""
        if use_ollama:
            try:
                output_content = await self.ollama_adapter.generate(
                    model=node.model_name or "llama3:8b",
                    prompt=incoming_payload,
                    system=node.system_prompt or f"You are a helpful {node.role.value} agent.",
                )
            except Exception:
                output_content = self.mock_adapter.generate_response(node.role.value, incoming_payload)
        else:
            output_content = self.mock_adapter.generate_response(node.role.value, incoming_payload)

        return {
            "node_id": node.node_id,
            "role": node.role.value,
            "output_content": output_content,
            "tool_calls": tool_calls_count,
            "blocked_actions": blocked_actions_count,
            "tool_results": tool_results,
        }
