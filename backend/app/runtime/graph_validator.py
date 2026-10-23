"""Server-side workflow topology and permission validator."""

from typing import List, Set
from ..schemas.workflow import WorkflowConfig, WorkflowValidationResult


class GraphValidator:
    """Validates structural and policy consistency of workflow definitions."""

    def validate(self, workflow: WorkflowConfig) -> WorkflowValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        node_ids: Set[str] = {node.node_id for node in workflow.nodes}

        # Verify entry node exists
        if workflow.entry_node_id not in node_ids:
            errors.append(f"Entry node '{workflow.entry_node_id}' does not exist in workflow nodes.")

        # Check edge endpoints exist
        for edge in workflow.edges:
            if edge.source_node_id not in node_ids:
                errors.append(f"Edge source '{edge.source_node_id}' is not a registered node.")
            if edge.target_node_id not in node_ids:
                errors.append(f"Edge target '{edge.target_node_id}' is not a registered node.")

        # Check peer authorization consistency
        for node in workflow.nodes:
            for peer in node.allowed_peers:
                if peer not in node_ids:
                    warnings.append(
                        f"Node '{node.node_id}' specifies allowed peer '{peer}' which is not in this workflow."
                    )

        return WorkflowValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
