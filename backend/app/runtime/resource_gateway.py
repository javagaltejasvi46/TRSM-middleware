"""Controlled Resource Gateway for tools, DB, and memory."""

import time
from typing import Optional, Tuple
from ..schemas.events import AuditEventType
from ..schemas.policy import PolicyDecision, PolicyDecisionEnum
from ..schemas.provenance import TrustLabel
from ..schemas.resources import ResourceActionRequest, ResourceActionResult
from ..schemas.workflow import WorkflowConfig
from ..trsm.policy_engine import PolicyEngine
from ..trsm.provenance import ProvenanceTracker
from ..audit.event_collector import AuditEventCollector
from .tool_registry import ToolRegistry


class ControlledResourceGateway:
    """Interception point for tools, database queries, and memory accesses."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        event_collector: Optional[AuditEventCollector] = None,
        tool_registry: Optional[ToolRegistry] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
    ):
        self.policy_engine = policy_engine or PolicyEngine()
        self.event_collector = event_collector or AuditEventCollector()
        self.tool_registry = tool_registry or ToolRegistry()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()

    async def mediate_action(
        self,
        request: ResourceActionRequest,
        workflow: Optional[WorkflowConfig] = None,
        enable_trsm: bool = True,
    ) -> Tuple[PolicyDecision, ResourceActionResult]:
        """Mediate a proposed tool, database, or memory action."""
        start_time = time.time()

        # 1. Audit event: Resource proposed
        await self.event_collector.emit(
            run_id=request.run_id,
            trace_id=request.trace_id,
            actor_id=request.requester_id,
            target_id=request.resource_name,
            event_type=AuditEventType.RESOURCE_PROPOSED,
            safe_payload_summary=f"Op: {request.operation}",
        )

        # Baseline mode bypasses TRSM evaluation
        if not enable_trsm:
            res_data = await self.tool_registry.execute(
                request.resource_name, request.operation, request.arguments
            )
            dur = (time.time() - start_time) * 1000.0
            prov = self.provenance_tracker.advance_lineage(
                current_record=request.provenance,
                current_node_id=request.resource_name,
                source_event_id=request.action_id,
                new_label=TrustLabel.TOOL_RESULT,
            )
            decision = PolicyDecision(
                request_id=request.action_id,
                outcome=PolicyDecisionEnum.ALLOW,
                reason_code="BASELINE_BYPASS",
            )
            result = ResourceActionResult(
                action_id=request.action_id,
                success=True,
                data=res_data,
                duration_ms=dur,
                provenance=prov,
            )
            await self.event_collector.emit(
                run_id=request.run_id,
                trace_id=request.trace_id,
                actor_id=request.requester_id,
                target_id=request.resource_name,
                event_type=AuditEventType.RESOURCE_EXECUTED,
                policy_decision=decision.outcome,
                reason_code=decision.reason_code,
                duration_ms=dur,
            )
            return decision, result

        # 2. Authoritative Policy Check
        decision = self.policy_engine.evaluate_resource_action(request, workflow)

        await self.event_collector.emit(
            run_id=request.run_id,
            trace_id=request.trace_id,
            actor_id="resource_gateway",
            target_id=request.resource_name,
            event_type=AuditEventType.RESOURCE_POLICY_DECIDED,
            policy_decision=decision.outcome,
            reason_code=decision.reason_code,
        )

        if decision.outcome != PolicyDecisionEnum.ALLOW:
            dur = (time.time() - start_time) * 1000.0
            prov = self.provenance_tracker.advance_lineage(
                current_record=request.provenance,
                current_node_id=request.requester_id,
                source_event_id=request.action_id,
                new_label=TrustLabel.VALIDATED,
            )
            result = ResourceActionResult(
                action_id=request.action_id,
                success=False,
                error=f"Blocked by TRSM: {decision.reason_code}",
                duration_ms=dur,
                provenance=prov,
            )
            await self.event_collector.emit(
                run_id=request.run_id,
                trace_id=request.trace_id,
                actor_id=request.requester_id,
                target_id=request.resource_name,
                event_type=AuditEventType.RESOURCE_BLOCKED,
                policy_decision=decision.outcome,
                reason_code=decision.reason_code,
                duration_ms=dur,
            )
            return decision, result

        # 3. Authorized Execution
        res_data = await self.tool_registry.execute(
            request.resource_name, request.operation, request.arguments
        )
        dur = (time.time() - start_time) * 1000.0
        prov = self.provenance_tracker.advance_lineage(
            current_record=request.provenance,
            current_node_id=request.resource_name,
            source_event_id=request.action_id,
            new_label=TrustLabel.TOOL_RESULT,
        )
        result = ResourceActionResult(
            action_id=request.action_id,
            success=True,
            data=res_data,
            duration_ms=dur,
            provenance=prov,
        )
        await self.event_collector.emit(
            run_id=request.run_id,
            trace_id=request.trace_id,
            actor_id=request.requester_id,
            target_id=request.resource_name,
            event_type=AuditEventType.RESOURCE_EXECUTED,
            policy_decision=decision.outcome,
            reason_code=decision.reason_code,
            duration_ms=dur,
        )
        return decision, result
