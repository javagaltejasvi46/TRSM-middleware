"""Integration tests for Communication Gateway and Resource Gateway."""

import asyncio
from app.runtime.communication_gateway import AgentCommunicationGateway
from app.runtime.resource_gateway import ControlledResourceGateway
from app.schemas.messages import AgentMessageProposal
from app.schemas.policy import PolicyDecisionEnum
from app.schemas.resources import ResourceActionRequest, ResourceActionType


def test_communication_gateway_blocks_undelivered_message(sample_workflow):
    """When a message is blocked, no envelope is delivered to the recipient."""
    async def _test():
        gw = AgentCommunicationGateway()
        proposal = AgentMessageProposal(
            run_id="run-int-1",
            trace_id="trace-int-1",
            sender_id="backend_agent",
            recipient_id="qa_agent",  # Unauthorized peer
            content="Secret message to QA",
        )
        decision, envelope = await gw.mediate_message(proposal, workflow=sample_workflow)
        assert decision.outcome == PolicyDecisionEnum.BLOCK
        assert envelope is None  # Critical invariant: receiver gets NOTHING

    asyncio.run(_test())


def test_resource_gateway_executes_allowed_action(sample_workflow):
    """Authorized tool invocation executes successfully and returns result."""
    async def _test():
        gw = ControlledResourceGateway()
        req = ResourceActionRequest(
            run_id="run-int-2",
            trace_id="trace-int-2",
            requester_id="backend_agent",
            resource_name="customer_db",
            operation="read_profile",
            arguments={"id": "1042"},
            action_type=ResourceActionType.DB_READ,
        )
        decision, result = await gw.mediate_action(req, workflow=sample_workflow)
        assert decision.outcome == PolicyDecisionEnum.ALLOW
        assert result.success is True
        assert result.data["id"] == "1042"

    asyncio.run(_test())
