from typing import Dict, Any, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from backend.app.contracts.workflow import WorkflowDefinition
from backend.app.runtime.agent_runner import AgentRunner

class WorkflowRuntimeState(TypedDict):
    current_node: str
    messages: Annotated[list, operator.add]
    data: Dict[str, Any]
    history: Annotated[list, operator.add]

def compile_workflow_to_langgraph(workflow: WorkflowDefinition):
    """
    Compiles a validated WorkflowDefinition into an executable LangGraph StateGraph.
    """
    builder = StateGraph(WorkflowRuntimeState)
    runners = {node.id: AgentRunner(node) for node in workflow.nodes}

    # Register each node
    for node in workflow.nodes:
        node_id = node.id
        runner = runners[node_id]

        def make_node_func(n_id, r):
            def node_func(state: WorkflowRuntimeState) -> Dict[str, Any]:
                current_data = state.get("data", {})
                last_msg = state.get("messages", [])[-1] if state.get("messages") else ""
                result = r.run(current_data, incoming_message=str(last_msg))
                
                new_msg = [result.output_message] if result.output_message else []
                new_history = [{
                    "node_id": n_id,
                    "status": result.status,
                    "output": result.output_message,
                    "error": result.error_message
                }]
                
                # Merge output data
                updated_data = dict(current_data)
                updated_data[f"{n_id}_output"] = result.output_message

                return {
                    "current_node": n_id,
                    "messages": new_msg,
                    "data": updated_data,
                    "history": new_history
                }
            return node_func

        builder.add_node(node_id, make_node_func(node_id, runner))

    # Entry point
    entry = workflow.entry_point or workflow.nodes[0].id
    builder.add_edge(START, entry)

    # Edges from workflow definition
    outgoing_edges = {node.id: [] for node in workflow.nodes}
    for edge in workflow.edges:
        outgoing_edges[edge.source].append(edge.target)
        builder.add_edge(edge.source, edge.target)

    # Any node with no outgoing edges transitions to END
    for node_id, targets in outgoing_edges.items():
        if not targets:
            builder.add_edge(node_id, END)

    return builder.compile()
