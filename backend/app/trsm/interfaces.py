from typing import Dict, Any, List
from backend.app.contracts.decisions import PolicyDecision, DecisionType, ThreatFinding
from backend.app.contracts.messages import AgentMessageProposal
from backend.app.contracts.resources import ResourceAction, ResourceType

class TRSMDecisionEngineInterface:
    """
    Interface agreed upon with Tejasvi.
    Provides pluggable hooks for Tejasvi's Guardian / Decision module.
    """
    def evaluate_agent_message(self, message: AgentMessageProposal, context: Dict[str, Any]) -> PolicyDecision:
        content_lower = message.content.lower()
        
        # Threat detection baseline
        if any(keyword in content_lower for keyword in ["inject_malicious", "drop table", "ignore previous instructions", "exfiltrate"]):
            return PolicyDecision(
                decision=DecisionType.BLOCK,
                reason_code="PROMPT_INJECTION_OR_UNTRUSTED_INSTRUCTION",
                policy_version="trsm-guardian-v1",
                threat_findings=[
                    ThreatFinding(
                        threat_type="prompt_injection",
                        severity="high",
                        details=f"Forbidden keyword detected in message from {message.sender}"
                    )
                ]
            )
        
        if "quarantine_test" in content_lower:
            return PolicyDecision(
                decision=DecisionType.QUARANTINE,
                reason_code="SUSPICIOUS_PAYLOAD_QUARANTINED",
                policy_version="trsm-guardian-v1"
            )

        if "review_test" in content_lower:
            return PolicyDecision(
                decision=DecisionType.REVIEW,
                reason_code="MANUAL_REVIEW_REQUIRED",
                policy_version="trsm-guardian-v1"
            )

        return PolicyDecision(
            decision=DecisionType.ALLOW,
            reason_code="POLICY_PASSED_BENIGN",
            policy_version="trsm-guardian-v1"
        )

    def evaluate_resource_action(self, action: ResourceAction, context: Dict[str, Any]) -> PolicyDecision:
        """
        Evaluate tool, database or memory operation against role allowlists,
        high-risk restrictions, and provenance boundaries.
        """
        # Rule 1: Arbitrary shell or filesystem access is strictly forbidden by default
        if action.resource_id in ["shell_exec", "file_system_write", "arbitrary_cmd"]:
            return PolicyDecision(
                decision=DecisionType.BLOCK,
                reason_code="HIGH_RISK_RESOURCE_FORBIDDEN",
                policy_version="trsm-guardian-v1",
                threat_findings=[
                    ThreatFinding(
                        threat_type="privilege_escalation",
                        severity="critical",
                        details=f"Actor '{action.actor_id}' attempted forbidden resource '{action.resource_id}'"
                    )
                ]
            )

        # Rule 2: Role-based boundary checks
        # Database operations require db_manager or backend role
        if action.action_type == ResourceType.DATABASE and action.actor_role not in ["db_manager", "backend"]:
            return PolicyDecision(
                decision=DecisionType.BLOCK,
                reason_code="ROLE_UNAUTHORIZED_FOR_DATABASE",
                policy_version="trsm-guardian-v1",
                threat_findings=[
                    ThreatFinding(
                        threat_type="unauthorized_access",
                        severity="medium",
                        details=f"Role '{action.actor_role}' is not authorized to perform direct database actions"
                    )
                ]
            )

        # Rule 3: Destructive operations check
        query = str(action.parameters.get("query", "")).lower()
        if "drop table" in query or "delete from" in query:
            return PolicyDecision(
                decision=DecisionType.BLOCK,
                reason_code="DESTRUCTIVE_DB_OPERATION_BLOCKED",
                policy_version="trsm-guardian-v1",
                threat_findings=[
                    ThreatFinding(
                        threat_type="data_destruction",
                        severity="critical",
                        details="Attempted destructive SQL statement"
                    )
                ]
            )

        return PolicyDecision(
            decision=DecisionType.ALLOW,
            reason_code="RESOURCE_ACTION_AUTHORIZED",
            policy_version="trsm-guardian-v1"
        )

# Default singleton instance (can be swapped with Tejasvi's real engine)
trsm_decision_engine = TRSMDecisionEngineInterface()
