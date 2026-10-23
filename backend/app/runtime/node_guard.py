"""TRSM Node Guard runtime wrapper."""

from typing import Any, Dict, Optional
from ..schemas.messages import AgentMessageProposal
from ..schemas.resources import ResourceActionRequest, ResourceActionType


class NodeGuard:
    """Runtime component wrapping agent execution and proposal creation."""

    def __init__(self, node_id: str, role: str):
        self.node_id = node_id
        self.role = role

    def create_message_proposal(
        self,
        recipient_id: str,
        content: str,
        run_id: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentMessageProposal:
        """Create a cryptographically tagged inter-agent message proposal."""
        return AgentMessageProposal(
            run_id=run_id,
            trace_id=trace_id,
            sender_id=self.node_id,
            recipient_id=recipient_id,
            content=content,
            metadata=metadata or {"guard_version": "1.0.0", "role": self.role},
        )

    def create_resource_request(
        self,
        resource_name: str,
        operation: str,
        arguments: Dict[str, Any],
        action_type: ResourceActionType,
        run_id: str,
        trace_id: str,
    ) -> ResourceActionRequest:
        """Create a controlled resource action request."""
        return ResourceActionRequest(
            run_id=run_id,
            trace_id=trace_id,
            requester_id=self.node_id,
            resource_name=resource_name,
            operation=operation,
            arguments=arguments,
            action_type=action_type,
        )
