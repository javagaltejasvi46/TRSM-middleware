"""Compiles workflow definitions into executable LangGraph StateGraphs with TRSM mediation."""

from typing import Any, Callable, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph

from ..audit.event_collector import AuditEventCollector
from ..schemas.policy import PolicyDecisionEnum
from ..schemas.workflow import WorkflowConfig
from .agent_runner import AgentRunner
from .communication_gateway import AgentCommunicationGateway
from .node_guard import NodeGuard
from .resource_gateway import ControlledResourceGateway


class WorkflowGraphState(TypedDict, total=False):
    """Execution state passed through the LangGraph runtime."""
    run_id: str
    trace_id: str
    current_node_id: str
    payload: str
    visited_nodes: List[str]
    step_count: int
    total_messages: int
    total_tool_calls: int
    blocked_actions: int
    status: str
    error: Optional[str]
    workflow_id: str
    enable_trsm: bool


class GraphCompiler:
    """Compiles a WorkflowConfig into an executable LangGraph StateGraph."""

    def __init__(
        self,
        comm_gateway: Optional[AgentCommunicationGateway] = None,
        resource_gateway: Optional[ControlledResourceGateway] = None,
        event_collector: Optional[AuditEventCollector] = None,
        agent_runner: Optional[AgentRunner] = None,
    ):
        self.comm_gateway = comm_gateway or AgentCommunicationGateway()
        self.resource_gateway = resource_gateway or ControlledResourceGateway()
        self.event_collector = event_collector or AuditEventCollector()
        self.agent_runner = agent_runner or AgentRunner(resource_gateway=self.resource_gateway)

    def compile(
        self,
        workflow: WorkflowConfig,
        enable_trsm: bool = True,
        use_ollama: bool = False,
    ):
        """Build and compile the LangGraph StateGraph with TRSM mediation."""
        graph_builder = StateGraph(WorkflowGraphState)
        node_map = {n.node_id: n for n in workflow.nodes}

        # 1. Register each agent node
        for node in workflow.nodes:
            def make_node_func(curr_node):
                async def node_func(state: WorkflowGraphState) -> Dict[str, Any]:
                    run_id = state.get("run_id", "default-run")
                    trace_id = state.get("trace_id", "default-trace")
                    payload = state.get("payload", "")
                    visited = list(state.get("visited_nodes", []))
                    visited.append(curr_node.node_id)

                    step_res = await self.agent_runner.execute_node(
                        node=curr_node,
                        incoming_payload=payload,
                        workflow=workflow,
                        run_id=run_id,
                        trace_id=trace_id,
                        enable_trsm=state.get("enable_trsm", enable_trsm),
                        use_ollama=use_ollama,
                    )

                    return {
                        "current_node_id": curr_node.node_id,
                        "payload": step_res["output_content"],
                        "visited_nodes": visited,
                        "step_count": state.get("step_count", 0) + 1,
                        "total_tool_calls": state.get("total_tool_calls", 0) + step_res["tool_calls"],
                        "blocked_actions": state.get("blocked_actions", 0) + step_res["blocked_actions"],
                    }

                return node_func

            graph_builder.add_node(node.node_id, make_node_func(node))

        # 2. Add entry edge from START to entry_node_id
        graph_builder.add_edge(START, workflow.entry_node_id)

        # 3. Inter-agent gateway nodes and conditional routing
        for node in workflow.nodes:
            outgoing = [e for e in workflow.edges if e.source_node_id == node.node_id]

            if not outgoing:
                graph_builder.add_edge(node.node_id, END)
                continue

            for edge in outgoing:
                src_id = edge.source_node_id
                tgt_id = edge.target_node_id
                gw_node_id = f"gw_{src_id}_to_{tgt_id}"

                def make_gw_func(source_id, target_id):
                    async def gw_func(state: WorkflowGraphState) -> Dict[str, Any]:
                        run_id = state.get("run_id", "default-run")
                        trace_id = state.get("trace_id", "default-trace")
                        payload = state.get("payload", "")
                        trsm_active = state.get("enable_trsm", enable_trsm)

                        guard = NodeGuard(source_id, node_map[source_id].role.value)
                        proposal = guard.create_message_proposal(
                            recipient_id=target_id,
                            content=payload,
                            run_id=run_id,
                            trace_id=trace_id,
                        )

                        decision, envelope = await self.comm_gateway.mediate_message(
                            proposal, workflow=workflow, enable_trsm=trsm_active
                        )

                        tot_msgs = state.get("total_messages", 0) + 1

                        if decision.outcome != PolicyDecisionEnum.ALLOW:
                            return {
                                "total_messages": tot_msgs,
                                "blocked_actions": state.get("blocked_actions", 0) + 1,
                                "status": "blocked",
                            }

                        return {
                            "total_messages": tot_msgs,
                            "payload": envelope.content if envelope else payload,
                        }

                    return gw_func

                graph_builder.add_node(gw_node_id, make_gw_func(src_id, tgt_id))
                graph_builder.add_edge(src_id, gw_node_id)

                def make_gw_router(target_id):
                    def gw_router(state: WorkflowGraphState) -> str:
                        if state.get("status") == "blocked":
                            return END
                        return target_id
                    return gw_router

                graph_builder.add_conditional_edges(
                    gw_node_id,
                    make_gw_router(tgt_id),
                    {tgt_id: tgt_id, END: END},
                )

        return graph_builder.compile()
