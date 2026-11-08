import uuid
import datetime
from typing import Dict, Any, Optional, List
from backend.app.contracts.resources import ResourceAction, ResourceExecutionResult, ResourceType
from backend.app.contracts.decisions import PolicyDecision, DecisionType
from backend.app.trsm.interfaces import trsm_decision_engine, TRSMDecisionEngineInterface
from backend.app.runtime.tool_registry import tool_registry, ToolRegistry

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
        threat_findings: list
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
            "threat_findings": self.threat_findings
        }

class ResourceGateway:
    """
    TRSM Resource Gateway for tools, database, and memory operations.
    Enforces authorization, allowlists, and execution boundaries.
    """
    def __init__(self, engine: Optional[TRSMDecisionEngineInterface] = None, registry: Optional[ToolRegistry] = None):
        self.engine = engine or trsm_decision_engine
        self.registry = registry or tool_registry
        self.event_log: List[ResourceGatewayEvaluationEvent] = []

    def execute(
        self,
        action: ResourceAction,
        run_id: str,
        trace_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[ResourceExecutionResult, ResourceGatewayEvaluationEvent]:
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
            "timestamp": timestamp
        }

        exec_result = ResourceExecutionResult(
            action_id=event_id,
            resource_id=action.resource_id,
            actor_id=action.actor_id,
            success=executed,
            result=result_payload,
            error=error_msg,
            provenance=provenance
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
            threat_findings=[f.model_dump() for f in decision.threat_findings]
        )

        self.event_log.append(gw_event)
        return exec_result, gw_event

resource_gateway = ResourceGateway()
