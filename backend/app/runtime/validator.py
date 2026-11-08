from typing import List, Set
from backend.app.contracts.workflow import WorkflowDefinition

SUPPORTED_NODE_TYPES = {"agent", "human", "resource"}
SUPPORTED_ROLES = {"backend", "db_manager", "qa", "devops", "supervisor", "coordinator"}

class WorkflowValidationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors

def validate_workflow_definition(workflow: WorkflowDefinition) -> List[str]:
    """
    Server-side validation for workflow graphs.
    Checks:
    1. At least one node exists.
    2. Node IDs are unique and non-empty.
    3. Node types are supported.
    4. Required role and model fields are non-empty.
    5. Edges refer only to declared node IDs (no dangling edges).
    6. Edge consistency with declared allowed_peers:
       An edge (A -> B) is only valid if B is listed in A's allowed_peers.
    7. Entry point (if specified) refers to a declared node.
    8. No self-loops unless explicitly permitted (default disallowed).
    """
    errors: List[str] = []

    if not workflow.nodes:
        errors.append("Workflow must contain at least one node.")
        return errors

    node_ids: Set[str] = set()
    node_map = {}

    for idx, node in enumerate(workflow.nodes):
        if not node.id or not node.id.strip():
            errors.append(f"Node at index {idx} has an empty or missing 'id'.")
            continue
        if node.id in node_ids:
            errors.append(f"Duplicate node ID detected: '{node.id}'.")
        node_ids.add(node.id)
        node_map[node.id] = node

        if node.node_type not in SUPPORTED_NODE_TYPES:
            errors.append(
                f"Node '{node.id}' has invalid node_type '{node.node_type}'. Supported: {sorted(SUPPORTED_NODE_TYPES)}"
            )

        if not node.role or not node.role.strip():
            errors.append(f"Node '{node.id}' must specify a non-empty 'role'.")

        if not node.model or not node.model.strip():
            errors.append(f"Node '{node.id}' must specify a non-empty 'model'.")

        # Validate that allowed_peers reference real nodes or will exist
        for peer in node.allowed_peers:
            if not peer or not peer.strip():
                errors.append(f"Node '{node.id}' has an empty peer ID in allowed_peers.")

    # Validate entry_point
    if workflow.entry_point:
        if workflow.entry_point not in node_ids:
            errors.append(f"entry_point '{workflow.entry_point}' does not match any declared node ID.")

    # Validate edges
    for idx, edge in enumerate(workflow.edges):
        if edge.source not in node_ids:
            errors.append(f"Edge index {idx}: source '{edge.source}' does not exist in declared nodes.")
        if edge.target not in node_ids:
            errors.append(f"Edge index {idx}: target '{edge.target}' does not exist in declared nodes.")

        if edge.source == edge.target:
            errors.append(f"Edge index {idx}: self-loop on node '{edge.source}' is not allowed.")

        # Enforcement: Edge source must have target in allowed_peers
        if edge.source in node_map and edge.target in node_ids:
            source_node = node_map[edge.source]
            if edge.target not in source_node.allowed_peers:
                errors.append(
                    f"Edge '{edge.source}' -> '{edge.target}' is unauthorized: "
                    f"'{edge.target}' is not in '{edge.source}' allowed_peers."
                )

    return errors
