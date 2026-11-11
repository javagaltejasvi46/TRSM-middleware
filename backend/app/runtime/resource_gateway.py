"""Controlled Resource Gateway for tools, DB, and memory."""

import datetime
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from backend.app.contracts.decisions import DecisionType, PolicyDecision
from backend.app.contracts.events import AuditEvent
from backend.app.contracts.resources import ResourceAction, ResourceExecutionResult, ResourceType
from backend.app.persistence.event_repository import EventRepository, event_repository
from backend.app.runtime.tool_registry import ToolRegistry, tool_registry
from backend.app.trsm.interfaces import TRSMDecisionEngineInterface, trsm_decision_engine


class ResourceGatewayEvaluationEvent:
    def __init__(
        self,
        event_id: str,
        run_id: str,
        trace_id: str,
        timestamp: str,
        action: ResourceAction,
        decision: DecisionType,
        reason_code: str,
        policy_version: str,
        executed: bool,
        threat_findings: list,
    ):
        self.event_id = event_id
        self.run_id = run_id
        self.trace_id = trace_id
        self.timestamp = timestamp
        self.action = action
        self.decision = decision
        self.reason_code = reason_code
        self.policy_version = policy_version
        self.executed = executed
        self.threat_findings = threat_findings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "actor_id": self.action.actor_id,
            "actor_role": self.action.actor_role,
            "resource_id": self.action.resource_id,
            "action_type": self.action.action_type.value,
            "decision": self.decision.value,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
            "executed": self.executed,
            "threat_findings": self.threat_findings,
        }


class ResourceGateway:
    """
    TRSM Resource Gateway for tools, database, and memory operations.
    Enforces authorization, allowlists, and execution boundaries.
    """

    def __init__(
        self,
        engine: Optional[TRSMDecisionEngineInterface] = None,
        registry: Optional[ToolRegistry] = None,
        repository: Optional[EventRepository] = None,
    ):
        self.engine = engine or trsm_decision_engine
        self.registry = registry or tool_registry
        self.repository = repository or event_repository
        self.event_log: List[ResourceGatewayEvaluationEvent] = []

    def execute(
        self,
        action: ResourceAction,
        run_id: str,
        trace_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ResourceExecutionResult, ResourceGatewayEvaluationEvent]:
        event_id = f"res-evt-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ctx = context or {}
        ctx.update({"run_id": run_id, "trace_id": trace_id})

        # Submit action to TRSM policy check
        decision: PolicyDecision = self.engine.evaluate_resource_action(action, ctx)

        executed = False
        result_payload = None
        error_msg = None

        if decision.decision == DecisionType.ALLOW:
            handler = self.registry.get_tool(action.resource_id)
            if handler:
                try:
                    result_payload = handler(action.parameters)
                    executed = True
                except Exception as ex:
                    error_msg = f"Execution error in '{action.resource_id}': {str(ex)}"
            else:
                error_msg = f"Resource handler for '{action.resource_id}' not found in registry."
        else:
            error_msg = f"Blocked by TRSM Resource Gateway: {decision.reason_code}"

        provenance = {
            "origin_actor": action.actor_id,
            "origin_role": action.actor_role,
            "resource_id": action.resource_id,
            "policy_decision": decision.decision.value,
            "timestamp": timestamp,
        }

        exec_result = ResourceExecutionResult(
            action_id=event_id,
            resource_id=action.resource_id,
            actor_id=action.actor_id,
            success=executed,
            result=result_payload,
            error=error_msg,
            provenance=provenance,
        )

        gw_event = ResourceGatewayEvaluationEvent(
            event_id=event_id,
            run_id=run_id,
            trace_id=trace_id,
            timestamp=timestamp,
            action=action,
            decision=decision.decision,
            reason_code=decision.reason_code,
            policy_version=decision.policy_version,
            executed=executed,
            threat_findings=[f.model_dump() for f in decision.threat_findings],
        )

        self.event_log.append(gw_event)

        # Persist structured audit event into SQLite
        audit_event = AuditEvent(
            event_id=event_id,
            run_id=run_id,
            trace_id=trace_id,
            parent_event_id=None,
            timestamp=timestamp,
            event_type="TOOL_EXECUTION",
            actor_id=action.actor_id,
            target_id=action.resource_id,
            source_type="resource_gateway",
            trust_labels=["tool_access"],
            policy_decision=decision.decision.value,
            reason_code=decision.reason_code,
            policy_version=decision.policy_version,
            duration_ms=1.2,
            safe_payload_summary=f"{action.resource_id} executed={executed}",
            payload_reference={
                "action_type": action.action_type.value,
                "executed": executed,
                "threat_findings": [f.model_dump() for f in decision.threat_findings],
            },
        )
        try:
            self.repository.insert_event(audit_event)
        except Exception:
            pass

        return exec_result, gw_event


resource_gateway = ResourceGateway()


# -------------------------------------------------------------------------
# Async ControlledResourceGateway for graph orchestrator & canonical schemas
# -------------------------------------------------------------------------
from ..audit.event_collector import AuditEventCollector
from ..schemas.events import AuditEventType
from ..schemas.policy import PolicyDecision as SchemaPolicyDecision, PolicyDecisionEnum
from ..schemas.provenance import TrustLabel
from ..schemas.resources import ResourceActionRequest, ResourceActionResult
from ..schemas.workflow import WorkflowConfig
from ..trsm.policy_engine import PolicyEngine
from ..trsm.provenance import ProvenanceTracker


class ControlledResourceGateway:
    """Interception point for tools, database queries, and memory accesses (Async Pipeline)."""

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
    ) -> Tuple[SchemaPolicyDecision, ResourceActionResult]:
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
            prov = request.provenance or self.provenance_tracker.create_initial_record()
            decision = SchemaPolicyDecision(
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
