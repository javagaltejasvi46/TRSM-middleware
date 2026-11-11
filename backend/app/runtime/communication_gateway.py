"""Central TRSM Agent Communication Gateway."""

import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.contracts.decisions import DecisionType, PolicyDecision
from backend.app.contracts.events import AuditEvent
from backend.app.contracts.messages import AgentMessageProposal
from backend.app.persistence.event_repository import EventRepository, event_repository
from backend.app.trsm.interfaces import TRSMDecisionEngineInterface, trsm_decision_engine


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

    def __init__(
        self,
        engine: Optional[TRSMDecisionEngineInterface] = None,
        repository: Optional[EventRepository] = None,
    ):
        self.engine = engine or trsm_decision_engine
        self.repository = repository or event_repository
        self.event_log: List[GatewayEvaluationEvent] = []

    def process_message(
        self,
        proposal: AgentMessageProposal,
        run_id: str,
        trace_id: str,
        parent_event_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], GatewayEvaluationEvent]:
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ctx = context or {}
        ctx.update({
            "run_id": run_id,
            "trace_id": trace_id,
            "sender": proposal.sender,
            "recipient": proposal.recipient,
        })

        # Submit to TRSM decision engine
        decision: PolicyDecision = self.engine.evaluate_agent_message(proposal, ctx)

        delivered = decision.decision == DecisionType.ALLOW
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
            threat_findings=[f.model_dump() for f in decision.threat_findings],
        )

        self.event_log.append(event)

        # Persist structured audit event into SQLite
        audit_event = AuditEvent(
            event_id=event_id,
            run_id=run_id,
            trace_id=trace_id,
            parent_event_id=parent_event_id,
            timestamp=timestamp,
            event_type="GATEWAY_DECISION",
            actor_id=proposal.sender,
            target_id=proposal.recipient,
            source_type="gateway",
            trust_labels=["inter_agent", "inspected"],
            policy_decision=decision.decision.value,
            reason_code=decision.reason_code,
            policy_version=decision.policy_version,
            duration_ms=0.5,
            safe_payload_summary=safe_preview,
            payload_reference={
                "delivered": delivered,
                "threat_findings": [f.model_dump() for f in decision.threat_findings],
            },
        )
        try:
            self.repository.insert_event(audit_event)
        except Exception:
            pass

        return delivered_content, event


communication_gateway = CentralCommunicationGateway()


# -------------------------------------------------------------------------
# Async AgentCommunicationGateway for graph orchestrator & canonical schemas
# -------------------------------------------------------------------------
from ..audit.event_collector import AuditEventCollector
from ..schemas.events import AuditEventType
from ..schemas.messages import (
    AgentMessageProposal as SchemaAgentMessageProposal,
    MessageDeliveryStatus,
    MessageEnvelope,
)
from ..schemas.policy import PolicyDecision as SchemaPolicyDecision, PolicyDecisionEnum
from ..schemas.workflow import WorkflowConfig
from ..trsm.policy_engine import PolicyEngine
from ..trsm.provenance import ProvenanceTracker


class AgentCommunicationGateway:
    """The central boundary intercepting every inter-agent message (Async Pipeline)."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        event_collector: Optional[AuditEventCollector] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.event_collector = event_collector or AuditEventCollector()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()

    async def mediate_message(
        self,
        proposal: SchemaAgentMessageProposal,
        workflow: Optional[WorkflowConfig] = None,
        enable_trsm: bool = True,
    ) -> Tuple[SchemaPolicyDecision, Optional[MessageEnvelope]]:
        """Mediate a proposed message from sender to recipient."""
        # 1. Audit event: Proposal received
        await self.event_collector.emit(
            run_id=proposal.run_id,
            trace_id=proposal.trace_id,
            actor_id=proposal.sender_id,
            target_id=proposal.recipient_id,
            event_type=AuditEventType.MESSAGE_PROPOSED,
            safe_payload_summary=proposal.content[:120],
        )

        # Baseline mode bypasses TRSM evaluation
        if not enable_trsm:
            prov = proposal.provenance or self.provenance_tracker.create_initial_record()
            decision = SchemaPolicyDecision(
                request_id=proposal.proposal_id,
                outcome=PolicyDecisionEnum.ALLOW,
                reason_code="BASELINE_BYPASS",
            )
            envelope = MessageEnvelope(
                proposal_id=proposal.proposal_id,
                run_id=proposal.run_id,
                trace_id=proposal.trace_id,
                sender_id=proposal.sender_id,
                recipient_id=proposal.recipient_id,
                content=proposal.content,
                provenance=prov,
                status=MessageDeliveryStatus.DELIVERED,
                policy_decision_id=decision.decision_id,
            )
            await self.event_collector.emit(
                run_id=proposal.run_id,
                trace_id=proposal.trace_id,
                actor_id=proposal.sender_id,
                target_id=proposal.recipient_id,
                event_type=AuditEventType.MESSAGE_DELIVERED,
                policy_decision=decision.outcome,
                reason_code=decision.reason_code,
            )
            return decision, envelope

        # 2. Authoritative Policy Decision
        decision = self.policy_engine.evaluate_message(proposal, workflow)

        # 3. Audit event: Policy decided
        await self.event_collector.emit(
            run_id=proposal.run_id,
            trace_id=proposal.trace_id,
            actor_id="communication_gateway",
            target_id=proposal.recipient_id,
            event_type=AuditEventType.MESSAGE_POLICY_DECIDED,
            policy_decision=decision.outcome,
            reason_code=decision.reason_code,
        )

        # 4. Handle Decision
        if decision.outcome == PolicyDecisionEnum.ALLOW:
            prov = self.provenance_tracker.advance_lineage(
                current_record=proposal.provenance,
                current_node_id=proposal.sender_id,
                source_event_id=proposal.proposal_id,
            )
            envelope = MessageEnvelope(
                proposal_id=proposal.proposal_id,
                run_id=proposal.run_id,
                trace_id=proposal.trace_id,
                sender_id=proposal.sender_id,
                recipient_id=proposal.recipient_id,
                content=proposal.content,
                provenance=prov,
                status=MessageDeliveryStatus.DELIVERED,
                policy_decision_id=decision.decision_id,
            )
            await self.event_collector.emit(
                run_id=proposal.run_id,
                trace_id=proposal.trace_id,
                actor_id=proposal.sender_id,
                target_id=proposal.recipient_id,
                event_type=AuditEventType.MESSAGE_DELIVERED,
                policy_decision=decision.outcome,
                reason_code=decision.reason_code,
            )
            return decision, envelope

        elif decision.outcome == PolicyDecisionEnum.QUARANTINE:
            await self.event_collector.emit(
                run_id=proposal.run_id,
                trace_id=proposal.trace_id,
                actor_id=proposal.sender_id,
                target_id=proposal.recipient_id,
                event_type=AuditEventType.MESSAGE_QUARANTINED,
                policy_decision=decision.outcome,
                reason_code=decision.reason_code,
            )
            return decision, None

        else:  # BLOCK
            await self.event_collector.emit(
                run_id=proposal.run_id,
                trace_id=proposal.trace_id,
                actor_id=proposal.sender_id,
                target_id=proposal.recipient_id,
                event_type=AuditEventType.MESSAGE_BLOCKED,
                policy_decision=decision.outcome,
                reason_code=decision.reason_code,
            )
            return decision, None
