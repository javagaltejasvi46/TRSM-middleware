import uuid
import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from backend.app.contracts.decisions import PolicyDecision, DecisionType
from backend.app.contracts.messages import AgentMessageProposal
from backend.app.trsm.interfaces import trsm_decision_engine, TRSMDecisionEngineInterface

class GatewayEvaluationEvent(BaseModel):
    event_id: str
    run_id: str
    trace_id: str
    parent_event_id: Optional[str] = None
    timestamp: str
    sender: str
    recipient: str
    decision: DecisionType
    reason_code: str
    policy_version: str
    delivered: bool
    safe_content_preview: Optional[str] = None
    threat_findings: list = Field(default_factory=list)

class CentralCommunicationGateway:
    """
    Central TRSM Agent Communication Gateway.
    Non-negotiable security boundary:
    No agent-to-agent message can reach its recipient without passing through here.
    """
    def __init__(self, engine: Optional[TRSMDecisionEngineInterface] = None):
        self.engine = engine or trsm_decision_engine
        self.event_log: List[GatewayEvaluationEvent] = []

    def process_message(
        self,
        proposal: AgentMessageProposal,
        run_id: str,
        trace_id: str,
        parent_event_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[Optional[str], GatewayEvaluationEvent]:
        """
        Intercepts proposed message, evaluates policy, logs structured event,
        and returns (delivered_content, event).
        If decision != ALLOW, delivered_content is None.
        """
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ctx = context or {}
        ctx.update({
            "run_id": run_id,
            "trace_id": trace_id,
            "sender": proposal.sender,
            "recipient": proposal.recipient
        })

        # Submit to TRSM decision engine
        decision: PolicyDecision = self.engine.evaluate_agent_message(proposal, ctx)

        delivered = (decision.decision == DecisionType.ALLOW)
        
        # Only allowed messages pass to recipient; blocked/quarantined messages are held outside
        delivered_content = proposal.content if delivered else None

        safe_preview = proposal.content[:80] if delivered else "[REDACTED_BY_TRSM_GATEWAY]"

        event = GatewayEvaluationEvent(
            event_id=event_id,
            run_id=run_id,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            timestamp=timestamp,
            sender=proposal.sender,
            recipient=proposal.recipient,
            decision=decision.decision,
            reason_code=decision.reason_code,
            policy_version=decision.policy_version,
            delivered=delivered,
            safe_content_preview=safe_preview,
            threat_findings=[f.model_dump() for f in decision.threat_findings]
        )

        self.event_log.append(event)
        return delivered_content, event

# Global communication gateway instance
communication_gateway = CentralCommunicationGateway()

