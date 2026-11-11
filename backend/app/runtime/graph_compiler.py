from typing import Dict, Any, TypedDict, Annotated, Optional
import operator
import uuid
from langgraph.graph import StateGraph, START, END
from backend.app.contracts.workflow import WorkflowDefinition
from backend.app.runtime.agent_runner import AgentRunner
from backend.app.runtime.communication_gateway import communication_gateway, CentralCommunicationGateway

class WorkflowRuntimeState(TypedDict):
    current_node: str
    messages: Annotated[list, operator.add]
    inbox: Dict[str, list]
    data: Dict[str, Any]
    history: Annotated[list, operator.add]
    gateway_events: Annotated[list, operator.add]

def compile_workflow_to_langgraph(
    workflow: WorkflowDefinition,
    run_id: str = "run-default",
    gateway: Optional[CentralCommunicationGateway] = None
):
    """
    Compiles a validated WorkflowDefinition into an executable LangGraph StateGraph.
    Enforces communication boundary:
    All inter-agent messages are routed through CentralCommunicationGateway.
    """
    gw = gateway or communication_gateway
    builder = StateGraph(WorkflowRuntimeState)
    runners = {node.id: AgentRunner(node) for node in workflow.nodes}

    # Register each node
    for node in workflow.nodes:
        node_id = node.id
        runner = runners[node_id]

        def make_node_func(n_id, r):
            def node_func(state: WorkflowRuntimeState) -> Dict[str, Any]:
                current_data = state.get("data", {})
                inbox = state.get("inbox", {})
                
                # Retrieve only delivered messages destined for this node
                node_inbox = inbox.get(n_id, [])
                incoming_msg = node_inbox[-1] if node_inbox else ""

                # Execute node logic
                result = r.run(current_data, incoming_message=incoming_msg)

                new_events = []
                updated_inbox = {k: list(v) for k, v in inbox.items()}

                # Intercept every proposed message through the gateway
                for prop in result.proposed_messages:
                    trace_id = f"trc-{uuid.uuid4().hex[:8]}"
                    delivered_content, gw_event = gw.process_message(
                        proposal=prop,
                        run_id=run_id,
                        trace_id=trace_id,
                        parent_event_id=None,
                        context={"executing_node": n_id}
                    )
                    new_events.append(gw_event.model_dump())

                    if delivered_content is not None:
                        # Deliver only to the target recipient's inbox
                        recipient_list = updated_inbox.setdefault(prop.recipient, [])
                        recipient_list.append(delivered_content)
                    else:
                        # Message is blocked/quarantined: never delivered to target agent context
                        pass

                new_history = [{
                    "node_id": n_id,
                    "status": result.status,
                    "output": result.output_message,
                    "error": result.error_message
                }]

                updated_data = dict(current_data)
                updated_data[f"{n_id}_output"] = result.output_message

                return {
                    "current_node": n_id,
                    "messages": [result.output_message] if result.output_message else [],
                    "inbox": updated_inbox,
                    "data": updated_data,
                    "history": new_history,
                    "gateway_events": new_events
                }
            return node_func

        builder.add_node(node_id, make_node_func(node_id, runner))

    # Entry point
    entry = workflow.entry_point or workflow.nodes[0].id
    builder.add_edge(START, entry)

    # Directed edges
    outgoing_edges = {node.id: [] for node in workflow.nodes}
    for edge in workflow.edges:
        outgoing_edges[edge.source].append(edge.target)
        builder.add_edge(edge.source, edge.target)

    # Any node with no outgoing edge transitions to END
    for node_id, targets in outgoing_edges.items():
        if not targets:
            builder.add_edge(node_id, END)

    return builder.compile()
