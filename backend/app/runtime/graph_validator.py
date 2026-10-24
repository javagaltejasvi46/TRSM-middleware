"""Server-side workflow topology and permission validator."""

from typing import List, Set
from ..schemas.workflow import WorkflowConfig, WorkflowValidationResult


class GraphValidator:
    """Validates structural and policy consistency of workflow definitions."""

    def validate(self, workflow: WorkflowConfig) -> WorkflowValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Node ID uniqueness and presence
        if not workflow.nodes:
            errors.append("Workflow must contain at least one agent node.")
            return WorkflowValidationResult(is_valid=False, errors=errors, warnings=warnings)

        seen_nodes: Set[str] = set()
        node_map = {}
        for node in workflow.nodes:
            if not node.node_id or not node.node_id.strip():
                errors.append("Node ID cannot be empty.")
                continue
            if node.node_id in seen_nodes:
                errors.append(f"Duplicate node ID detected: '{node.node_id}'.")
            seen_nodes.add(node.node_id)
            node_map[node.node_id] = node

            # Validate role presence
            if not node.role:
                errors.append(f"Node '{node.node_id}' is missing a valid AgentRole.")

        # 2. Verify entry node exists
        if not workflow.entry_node_id or workflow.entry_node_id not in seen_nodes:
            errors.append(f"Entry node '{workflow.entry_node_id}' does not exist in workflow nodes.")

        # 3. Check edges
        seen_edges: Set[tuple] = set()
        for edge in workflow.edges:
            edge_pair = (edge.source_node_id, edge.target_node_id)
            if edge_pair in seen_edges:
                warnings.append(f"Duplicate edge detected from '{edge.source_node_id}' to '{edge.target_node_id}'.")
            seen_edges.add(edge_pair)

            # Check self-loops
            if edge.source_node_id == edge.target_node_id:
                errors.append(f"Self-loop detected on node '{edge.source_node_id}'. Direct self-communication is disallowed.")

            # Check endpoints exist
            if edge.source_node_id not in seen_nodes:
                errors.append(f"Edge source '{edge.source_node_id}' is not a registered node.")
            if edge.target_node_id not in seen_nodes:
                errors.append(f"Edge target '{edge.target_node_id}' is not a registered node.")

            # Check policy consistency: source node must list target in allowed_peers
            source_node = node_map.get(edge.source_node_id)
            if source_node and edge.target_node_id not in source_node.allowed_peers:
                warnings.append(
                    f"Edge declared from '{edge.source_node_id}' to '{edge.target_node_id}', "
                    f"but '{edge.target_node_id}' is not in source node's allowed_peers list."
                )

        # 4. Check peer authorization consistency
        for node in workflow.nodes:
            for peer in node.allowed_peers:
                if peer not in seen_nodes:
                    warnings.append(
                        f"Node '{node.node_id}' specifies allowed peer '{peer}' which is not in this workflow."
                    )

        return WorkflowValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
