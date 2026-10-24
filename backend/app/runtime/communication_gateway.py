"""Central TRSM Agent Communication Gateway."""

from typing import Optional, Tuple
from uuid import uuid4
from ..persistence.review_repository import ReviewRepository
from ..schemas.events import AuditEventType
from ..schemas.messages import AgentMessageProposal, MessageDeliveryStatus, MessageEnvelope
from ..schemas.policy import PolicyDecision, PolicyDecisionEnum
from ..schemas.workflow import WorkflowConfig
from ..trsm.policy_engine import PolicyEngine
from ..trsm.provenance import ProvenanceTracker
from ..audit.event_collector import AuditEventCollector


class AgentCommunicationGateway:
    """The central boundary intercepting every inter-agent message."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        event_collector: Optional[AuditEventCollector] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        review_repo: Optional[ReviewRepository] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.event_collector = event_collector or AuditEventCollector()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()
        self.review_repo = review_repo or ReviewRepository()

    async def mediate_message(
        self,
        proposal: AgentMessageProposal,
        workflow: Optional[WorkflowConfig] = None,
        enable_trsm: bool = True,
    ) -> Tuple[PolicyDecision, Optional[MessageEnvelope]]:
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
            decision = PolicyDecision(
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

        elif decision.outcome == PolicyDecisionEnum.REVIEW:
            # Create pending human review record
            try:
                await self.review_repo.create_review(
                    review_id=str(uuid4()),
                    run_id=proposal.run_id,
                    trace_id=proposal.trace_id,
                    event_id=proposal.proposal_id,
                    actor_id=proposal.sender_id,
                    action_type="inter_agent_message",
                    target=proposal.recipient_id,
                )
            except Exception:
                pass

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
